from rest_framework.response import Response
from rest_framework import status, viewsets

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.conf import settings
import os
import joblib

from categories.models import CategoriesModel


# Create your views here.
class ForDeveloperView(viewsets.ModelViewSet):

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='name')])
    def get(self, request):
        name = request.GET.get('name', None)
        model_name = 'main_category'
        predicted_category = None
        if name is not None:
            model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{model_name}.pkl')
            model = joblib.load(model_path)
            predicted_category = model.predict([name])[0]
            print(f"En uygun kategori: {predicted_category}")

            category1 = CategoriesModel.objects.filter(name__iexact=predicted_category, shop__isnull=True).first()
            model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category1.id}_category.pkl')
            model = joblib.load(model_path)
            predict = model.predict([name])[0]
            predicted_category1 = predict_fix_unicode(predict)
            is_exist = CategoriesModel.objects.filter(parent=category1.id, is_deleted=False).exists()
            predicted_category2 = None
            if is_exist:
                category2 = CategoriesModel.objects.filter(name__iexact=predicted_category1, shop__isnull=True).first()
                print(category2)
                model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category2.id}_category.pkl')
                model = joblib.load(model_path)
                predict = model.predict([name])[0]
                predicted_category2 = predict_fix_unicode(predict)

        return Response({'success': True, 'predict': f'{predicted_category} > {predicted_category1} > {predicted_category2}'})

#TODO
# Daha sonra utilse taşınacak
def predict_fix_unicode(predict):
    if predict == 'gıda & içecek':
        predict = 'gıda & İçecek'
    if predict == 'iç giyim':
        predict = 'İç giyim'
    if predict == 'içecek hazırlama':
        predict = 'İçecek hazırlama'
    if predict == 'araç içi aksesuarı':
        predict = 'araç İçi aksesuarı'
    if predict == 'araç içi telefon tutucu':
        predict = 'araç İçi telefon tutucu'
    if predict == 'dolap içi düzenleyici':
        predict = 'dolap İçi düzenleyici'
    if predict == 'sinek ilacı ve kovucu':
        predict = 'sinek İlacı ve kovucu'

    return predict