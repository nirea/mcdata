import mongoengine as mg


# This is the max number of bytes you can receive in the body of LSL's
# http_response.  It's also the max number of bytes we'll store for any one
# avatar.
MAX_SIZE = 2048


class Av(mg.Document):
    key=mg.StringField(max_length=36, unique=True, required=True)
    username=mg.StringField(max_length=63)
    owners=mg.ListField(mg.ReferenceField('Av'))

    meta = {
        'allow_inheritance': False,
    }

    def __unicode__(self):
        if self.username:
            return self.username
        else:
            return self.key

    def to_owner(self):
        return '%s,%s' % (self.key, self.username)

    def has_owner(self, key):
        """Determine whether av identified by 'key' is an owner of self."""
        return any(o.key==key for o in self.owners)
    
    def to_lsl(self):
        """
        Return "key=val" newline-delimited string for easy parsing by LSL
        scripts.
        """

        out = ["key=" + self.key]
        out += ["username=" + self.username]
        out += ["owners=" + ",".join([o.to_owner() for o in self.owners])]
        return "&".join(out)

    @property
    def size(self):
        """Serialize and return len() of the resulting string.  Used for
        checking storage quotas."""
        return len(self.to_lsl())

    # TODO: a delete() method that also removes references from anyone's owners
    # list.
