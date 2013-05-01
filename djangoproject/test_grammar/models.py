from django.db import models

# TODO: Metadata() in SQLAlchemy -> subclass Meta in Django
# TODO: get_absolute_url()
# TODO: precise the max_length's

# use a string instead of this?
class Message(models.Model):
    text = models.CharField(max_length=1000)
    
    def __unicode__(self):
        return self.text[:15]

class Notes(models.Model):
    text = models.CharField(max_length=1000)
    
    def __unicode__(self):
        return self.text[:15]
# //

class Hash(models.Model):
    alg = models.CharField(max_length=200)
    hexdigest = models.CharField(max_length=1000)
    
    def __unicode__(self):
        return self.alg + ": " + self.hexdigest[:15]

class File(models.Model):
    givenpath = models.CharField(max_length=200)
    abspath = models.CharField(max_length=200) # optional
    hash = models.ForeignKey(Hash) # optional
    
    def __unicode__(self):
        return self.givenpath

class Function(models.Model):
    name = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.name

class Point(models.Model):
    line = models.IntegerField()
    column = models.IntegerField()
    
    def __unicode__(self):
        return self.line + ":" + self.column

class Range(models.Model):
    start = models.ForeignKey(Point, related_name='range_start')
    end = models.ForeignKey(Point, related_name='range_end')
    
    def __unicode__(self):
        return self.start + " to " + self.end

class Location(models.Model):
    file = models.ForeignKey(File)
    function = models.ForeignKey(Function) # optional
    point = models.ForeignKey(Point) # either point or range
    range = models.ForeignKey(Range)
    
    def __unicode__(self):
        place = self.point if self.point != None else self.range
        return self.file + ":" + self.function + ":" + place

class Trace(models.Model):
    pass

class State(models.Model):
    trace = models.ForeignKey(Trace)
    location = models.ForeignKey(Location)
    notes = models.ForeignKey(Notes) # optional
    # TODO: annotations(key/value pairs)
    
    def __unicode__(self):
        return self.location + " (" + self.notes[:15] + ")"

class Customfields(models.Model):
    pass

class Customfield(models.Model):
    customfields = models.ForeignKey(Customfields)

class Intfield(Customfield):
    name = models.CharField(max_length=200)
    value = models.IntegerField()
    
    def __unicode__(self):
        return self.name + " = " + self.value

class Strfield(Customfield):
    name = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.name + " = " + self.value

class Generator(models.Model):
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=200) # optional
    
    def __unicode__(self):
        if self.version:
            return self.name + ": " + self.version
        else:
            return self.name

# single-table inheritance (like firehose-orm)
class Sut(models.Model): # sut = software under test
    type = models.CharField(max_length=20) # nullable=False??
    # Choices: source-rpm, debian-source, debian-binary
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=200)
    release = models.CharField(max_length=200) # optional for debian-src/bin
    buildarch = models.CharField(max_length=200) # not for debian-src
    # -> ForeignKey for the archs?
    
    def __unicode__(self):
        sutcode = self.name + " " + self.version
        if self.release:
            sutcode += " (" + self.release + ")"
        if self.buildarch:
            sutcode += " (" + self.buildarch + ")"
        return sutcode

class Stats(models.Model):
    wallclocktime = models.FloatField()
    
    def __unicode__(self):
        return self.wallclocktime

class Metadata(models.Model):
    generator = models.ForeignKey(Generator)
    sut = models.ForeignKey(Sut)
    file = models.ForeignKey(File) # optional
    stats = models.ForeignKey(Stats) # optional
    
    def __unicode__(self):
        return self.generator + " - " \
            + self.sut + " - " \
            + self.file + " - " \
            + self.stats

class Analysis(models.Model):
    metadata = models.ForeignKey(Metadata)
    customfields = models.ForeignKey(Customfields) # optional
    
    def __unicode__(self):
        return self.id

class Result(models.Model):
    analysis = models.ForeignKey(Analysis)
    
# multi-table inheritance (one-to-one field automatically provided by Django)
class Issue(Result):
    cwe = models.IntegerField() # optional
    testid = models.CharField(max_length=200) # optional
    location = models.ForeignKey(Location)
    message = models.ForeignKey(Message)
    notes = models.ForeignKey(Notes) # optional
    trace = models.ForeignKey(Trace) # optional
    severity = models.CharField(max_length=200) # optional
    customfields = models.ForeignKey(Customfields) # optional
    
    def __unicode__(self):
        return "issue " + self.id

class Failure(Result):
    failureid = models.CharField(max_length=200) # optional
    location = models.ForeignKey(Location) # optional
    message = models.ForeignKey(Message) # optional
    customfields = models.ForeignKey(Customfields) # optional
    
    def __unicode__(self):
        return "failure " + self.id

class Info(Result):
    infoid = models.CharField(max_length=200) # optional
    location = models.ForeignKey(Location) # optional
    message = models.ForeignKey(Message) # optional
    customfields = models.ForeignKey(Customfields) # optional
    
    def __unicode__(self):
        return "info " + self.id
