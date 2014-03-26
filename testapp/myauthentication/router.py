class MyDatabaseRouter(object):
    """
        A router to manage database operations in the myauthentication app.
    """
    def db_for_read(self, model, **hints):
		"""
			Point all read operations on myauthentication app to spoken
			database.
		"""
		if model._meta.app_label == 'myauthentication':
			return 'spoken'
		return None
