from django.db import models

from ..constants import StringLength

class User(models.Model):
    user_id = models.CharField(max_length=StringLength.SHORT.value, primary_key=True)
    full_name = models.CharField(max_length=StringLength.EXTRA_LONG.value)
    email = models.EmailField(max_length=StringLength.LONG.value, unique=True)
    phone = models.CharField(max_length=StringLength.SHORT.value)
    password = models.CharField(max_length=StringLength.DESCRIPTION.value)
    role = models.ForeignKey('Role', on_delete=models.RESTRICT, db_column='role_id')
    province = models.ForeignKey('Province', on_delete=models.RESTRICT, null=True, blank=True, db_column='province_id')
    district = models.ForeignKey('District', on_delete=models.RESTRICT, null=True, blank=True, db_column='district_id')
    ward = models.ForeignKey('Ward', on_delete=models.RESTRICT, null=True, blank=True, db_column='ward_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    detail_address = models.CharField(max_length=StringLength.ADDRESS.value, null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.full_name
