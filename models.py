import mongoengine as mg


# This is the max number of bytes you can receive in the body of LSL's
# http_response.  It's also the max number of bytes we'll store for any one
# avatar.
MAX_SIZE = 2048


class Owner(mg.EmbeddedDocument):
    key=mg.StringField(max_length=36, unique=True, required=True)
    name=mg.StringField(max_length=63)

    def to_owner(self):
        return '%s,%s' % (self.key, self.name)

    meta = {
        'allow_inheritance': False
    }


class Av(mg.Document):
    key=mg.StringField(max_length=36, unique=True, required=True)
    owners=mg.ListField(mg.EmbeddedDocumentField(Owner))

    meta = {
        'allow_inheritance': False,
    }

    def __unicode__(self):
        return self.key

    def has_owner(self, key):
        """Determine whether av identified by 'key' is an owner of self."""
        return any(o.key==key for o in self.owners)
    
    def to_lsl(self):
        """
        Return "key=val" newline-delimited string for easy parsing by LSL
        scripts.
        """
        
        return '\n'.join([
            "MCDATA " + self.key, # MCDATA header
            "owners=" + ",".join([o.to_owner() for o in self.owners])
        ])

    @property
    def size(self):
        """Serialize and return len() of the resulting string.  Used for
        checking storage quotas."""
        return len(self.to_lsl())

    # TODO: a delete() method that also removes references from anyone's owners
    # list.

    # TODO: enforce MAX_SIZE quotas on save
