from flask.ext.wtf import Form, SelectField, TextField, Required

class SearchForm(Form):
    packagename = TextField('package name', validators=[])
    packageversion = SelectField('package version', choices=[('', '(all)')])
    generatorname = SelectField('generator name')
    generatorversion = SelectField('generator version', choices=[('', '(all)')])
    
