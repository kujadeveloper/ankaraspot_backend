class MyRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'training_data':
            return 'mongo'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'training_data':
            return 'mongo'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'training_data':
            return db == 'mongo'
        return db == 'default'
