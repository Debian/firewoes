from django.contrib import admin
import test_grammar.models as g

# gets all the classes from the model
classes = list([(cls) for name, cls in g.__dict__.items() if isinstance(cls, type)])

for c in classes:
    admin.site.register(c)
