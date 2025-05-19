from django.db import migrations

def add_cities_spec(apps, schema_editor):
    SpecsModel = apps.get_model('specs', 'SpecsModel')
    SpecValueModel = apps.get_model('specs', 'SpecValueModel')

    cities_spec = SpecsModel.objects.create(
        name="İller",
        is_active=True
    )
    
    turkish_cities = [
        "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
        "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
        "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari",
        "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir",
        "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir",
        "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat",
        "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
        "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye",
        "Düzce"
    ]
    
    for city in turkish_cities:
        SpecValueModel.objects.create(
            value=city,
            specs=cities_spec,
            is_active=True
        )

def remove_cities_spec(apps, schema_editor):
    SpecsModel = apps.get_model('specs', 'SpecsModel')
    SpecsModel.objects.filter(name="İller").delete()

class Migration(migrations.Migration):
    dependencies = [
        ('specs', '0006_specvaluemodel_specs_alter_specsmodel_created_at_and_more'),
    ]

    operations = [
        migrations.RunPython(add_cities_spec, remove_cities_spec),
    ] 