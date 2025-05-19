import boto3
import os
import io
import requests
import datetime
import urllib3

from PIL import Image

from sitesettings.models import SitesettingsModels
from google.cloud import storage
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from utils.product_data import ProductSave

class S3:
    CDN_ENDPOINT = None

    def __init__(self):
        site_settings = SitesettingsModels.objects.first()
        self.AWS_ACCESS_KEY_ID = site_settings.aws_access_key
        self.AWS_SECRET_ACCESS_KEY = site_settings.aws_secret
        self.CDN_ENDPOINT = site_settings.aws_url
        self.bucket_name = site_settings.bucket
        self.session = boto3.Session(
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )
        self.s3_client = self.session.client('s3', endpoint_url=self.CDN_ENDPOINT,
                                             config=boto3.session.Config(signature_version='s3v4'))
        self.product_save = ProductSave()
    def send_file(self, file, filename, folder):
        if folder is not None:
            filename = str(folder) + "/" + filename
        self.s3_client.put_object(Body=file, Bucket=self.bucket_name, Key=filename)
        return self.CDN_ENDPOINT + '/' + self.bucket_name + '/' + filename

    def get_file(self, filename):
        file_byte_string = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)['Body'].read()
        return io.BytesIO(file_byte_string)

    def get_file_url(self, filename, userid):
        filename = filename
        # bucket_location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
        # object_url = "https://s3-{0}.amazon_aws.com/{1}/{2}".format(
        # bucket_location['LocationConstraint'],
        # self.bucket_name,
        # filename)
        object_url = self.s3_client.generate_presigned_url('get_object', ExpiresIn=0,
                                                           Params={'Bucket': self.bucket_name, 'Key': filename})
        return object_url

    def download_and_resize_image(self, url, max_size=(360, 360)):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session = requests.Session()
            retry = Retry(
                total=5,  # Total number of retries
                backoff_factor=1,  # Time to wait between retries
                status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
                allowed_methods=["HEAD", "GET", "OPTIONS"]  # Retry only for these methods
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            response = session.get(url, stream=True, headers=self.product_save.headers, verify=False)
            # Send an HTTP GET request to the URL
            if response.status_code != 200:
                print(f"Failed to download image from {url}. Status code: {response.status_code}")
                return None, None, None

            # Open the image from the response content
            image = Image.open(io.BytesIO(response.content))

            # Get the original image dimensions
            original_width, original_height = image.size

            # Check if resizing is needed
            if original_width > max_size[0] or original_height > max_size[1]:
                # Calculate the proportional resizing factor
                resize_factor = min(max_size[0] / original_width, max_size[1] / original_height)

                # Calculate the new size based on the resizing factor
                new_size = (int(original_width * resize_factor), int(original_height * resize_factor))

                # Resize the image
                image = image.resize(new_size, Image.LANCZOS)

            # Generate a unique filename for the resized image
            current_time = datetime.datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            url_without_query = url.split('?')[0]
            filename = f'{url_without_query}'
            filename = filename.split('/')[-1]
            base_name, extension = os.path.splitext(filename)
            filename = f'{base_name}{extension}'
            filename = f"{timestamp}_{filename}"

            if image.mode == 'RGBA':
                image = image.convert('RGB')
            # Save the resized image
            image_bytes = io.BytesIO()

            image.save(image_bytes, format('JPEG'))
            image_bytes.seek(0)
            # Get the file size of the resized image
            resized_file_size = 0
            #os.remove(filename)
            return image_bytes, filename,resized_file_size

        except Exception as e:
            print(f"Error: {e}")
            return None, None, None


class Cloud:
    google_application_credentials = 'lms-4ce08614bea7.json'  #json file
    bucket_name = 'lms'

    def upload_image_to_gcs(self, source_file_name, destination_blob_name, file):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.google_application_credentials
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_file(file, content_type=file.content_type)
        #blob.make_public()
        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
        return blob.public_url
