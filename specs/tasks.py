from celery import shared_task

@shared_task
def spec_progress(datas):
    from products.models import ProductModel
    from specs.models import SpecsModel
    for data in datas:
        if 'spects' in data:
            product = ProductModel.objects.filter(link=data['link']).first()
            if product:
                for feature in data['spects']:
                    title = feature['title'].encode('utf-8').decode('utf-8').lower()
                    values = feature['value']
                    is_specs = SpecsModel.objects.filter(name=title, is_deleted=False).first()
                    if is_specs is None:
                        is_specs = SpecsModel.objects.create(name=title, shop=product.shop)

                    for value in values:
                        is_value = is_specs.value.filter(value=value, is_deleted=False).first()
                        if is_value is None:
                            is_value = is_specs.value.create(value=value, shop=product.shop)
                        is_specs.value.add(is_value)

                        # spec value products içinde tanımlı değilse tanımla
                        is_product_spec_value = product.spec_values.filter(value=is_value, is_deleted=False).first()
                        if is_product_spec_value is None:
                            product.spec_values.add(is_value)

                    # category yok ise spec içine tanımla
                    is_category_spec = product.category.specs.filter(id=is_specs.id, is_deleted=False).first()
                    if is_category_spec is None:
                        product.category.specs.add(is_specs)