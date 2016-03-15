# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models


class TArea(models.Model):
    id_area = models.AutoField(primary_key=True)
    area_name = models.CharField(unique=True, max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_AREA'


class TBoards(models.Model):
    id_board = models.IntegerField(primary_key=True)
    t_board_type_id_board_type = models.ForeignKey('TBoardType', db_column='T_BOARD_TYPE_id_board_type')  # Field name made lowercase.
    t_equipment_id_equipment = models.ForeignKey('TEquipment', db_column='T_EQUIPMENT_id_equipment', blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(max_length=255, blank=True, null=True)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'T_BOARDS'


class TBoardType(models.Model):
    id_board_type = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=45)
    description = models.CharField(max_length=255, blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_BOARD_TYPE'


class TDomain(models.Model):
    id_domain = models.AutoField(primary_key=True)
    t_sw_rel_id_sw_rel = models.ForeignKey('TSwRel', db_column='T_SW_REL_id_sw_rel')  # Field name made lowercase.
    t_prod_id_prod = models.ForeignKey('TProd', db_column='T_PROD_id_prod')  # Field name made lowercase.
    t_area_id_area = models.ForeignKey(TArea, db_column='T_AREA_id_area')  # Field name made lowercase.
    t_scope_id_scope = models.ForeignKey('TScope', db_column='T_SCOPE_id_scope')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_DOMAIN'


class TEpic(models.Model):
    id_epic = models.AutoField(primary_key=True)
    epic_reference = models.CharField(max_length=45)
    t_prod_id_prod = models.ForeignKey('TProd', db_column='T_PROD_id_prod')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_EPIC'


class TEqptBooking(models.Model):
    id_booking = models.AutoField(primary_key=True)
    t_equipment_id_equipment = models.ForeignKey('TEquipment', db_column='T_EQUIPMENT_id_equipment')  # Field name made lowercase.
    user = models.CharField(max_length=45)
    datefrom = models.DateField(db_column='dateFROM', blank=True, null=True)  # Field name made lowercase.
    dateto = models.DateField(db_column='dateTO', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_EQPT_BOOKING'


class TEquipment(models.Model):
    id_equipment = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=45)
    t_equip_type_id_type = models.ForeignKey('TEquipType', db_column='T_EQUIP_TYPE_id_type')  # Field name made lowercase.
    t_location_id_location = models.ForeignKey('TLocation', db_column='T_LOCATION_id_location')  # Field name made lowercase.
    t_scope_id_scope = models.ForeignKey('TScope', db_column='T_SCOPE_id_scope')  # Field name made lowercase.
    t_packages_id_pack = models.ForeignKey('TPackages', db_column='T_PACKAGES_id_pack', blank=True, null=True)  # Field name made lowercase.
    owner = models.CharField(max_length=45, blank=True, null=True)
    inuse = models.IntegerField(db_column='inUse', blank=True, null=True)  # Field name made lowercase.
    description = models.CharField(max_length=64, blank=True, null=True)
    note = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_EQUIPMENT'


class TEquipType(models.Model):
    id_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    description = models.CharField(max_length=45, blank=True, null=True)
    family = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'T_EQUIP_TYPE'


class TJiraStory(models.Model):
    story_reference = models.CharField(primary_key=True, max_length=45)
    t_epic_id_epic = models.ForeignKey(TEpic, db_column='T_EPIC_id_epic')  # Field name made lowercase.
    t_domain_id_domain = models.ForeignKey(TDomain, db_column='T_DOMAIN_id_domain')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_JIRA_STORY'


class TLocation(models.Model):
    id_location = models.AutoField(primary_key=True)
    site = models.CharField(max_length=45, blank=True, null=True)
    room = models.CharField(max_length=45, blank=True, null=True)
    row = models.CharField(max_length=45, blank=True, null=True)
    rack = models.IntegerField(blank=True, null=True)
    pos = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_LOCATION'


class TNet(models.Model):
    id_ip = models.AutoField(primary_key=True)
    inuse = models.IntegerField(db_column='inUse')  # Field name made lowercase.
    description = models.CharField(max_length=45, blank=True, null=True)
    t_equipment_id_equipment = models.ForeignKey(TEquipment, db_column='T_EQUIPMENT_id_equipment', blank=True, null=True)  # Field name made lowercase.
    protocol = models.CharField(max_length=2)
    ip = models.CharField(db_column='IP', max_length=45)  # Field name made lowercase.
    nm = models.CharField(db_column='NM', max_length=45, blank=True, null=True)  # Field name made lowercase.
    gw = models.CharField(db_column='GW', max_length=45, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_NET'


class TPackages(models.Model):
    id_pack = models.AutoField(primary_key=True)
    laboratory = models.CharField(max_length=16)
    name = models.CharField(max_length=255)
    fromdevel = models.DateTimeField(db_column='fromDevel')  # Field name made lowercase.
    tovalid = models.DateTimeField(db_column='toValid', blank=True, null=True)  # Field name made lowercase.
    todr4 = models.DateTimeField(db_column='toDR4', blank=True, null=True)  # Field name made lowercase.
    t_sw_rel_id_sw_rel = models.ForeignKey('TSwRel', db_column='T_SW_REL_id_sw_rel')  # Field name made lowercase.
    t_prod_id_prod = models.ForeignKey('TProd', db_column='T_PROD_id_prod')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_PACKAGES'


class TPresets(models.Model):
    id_preset = models.AutoField(primary_key=True)
    owner = models.CharField(max_length=45)
    preset_description = models.CharField(max_length=255)
    preset_title = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'T_PRESETS'


class TProd(models.Model):
    id_prod = models.AutoField(primary_key=True)
    product = models.CharField(unique=True, max_length=45)

    class Meta:
        managed = False
        db_table = 'T_PROD'


class TPstEntity(models.Model):
    id_preset_entity = models.AutoField(primary_key=True)
    t_tpy_entity_id_entity = models.ForeignKey('TTpyEntity', db_column='T_TPY_ENTITY_id_entity')  # Field name made lowercase.
    t_presets_id_preset = models.ForeignKey(TPresets, db_column='T_PRESETS_id_preset')  # Field name made lowercase.
    t_equipment_id_equipment = models.ForeignKey(TEquipment, db_column='T_EQUIPMENT_id_equipment')  # Field name made lowercase.
    pstvalue = models.CharField(db_column='pstValue', max_length=45, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_PST_ENTITY'


class TReport(models.Model):
    id_report = models.AutoField(primary_key=True)
    t_packages_id_pack = models.ForeignKey(TPackages, db_column='T_PACKAGES_id_pack')  # Field name made lowercase.
    t_tps_id_tps = models.ForeignKey('TTps', db_column='T_TPS_id_tps')  # Field name made lowercase.
    info = models.TextField(blank=True, null=True)
    result = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_REPORT'


class TRtmBody(models.Model):
    t_runtime_id_run = models.IntegerField(db_column='T_RUNTIME_id_run')  # Field name made lowercase.
    t_equipment_id_equipment = models.IntegerField(db_column='T_EQUIPMENT_id_equipment')  # Field name made lowercase.
    t_packages_id_pack = models.IntegerField(db_column='T_PACKAGES_id_pack')  # Field name made lowercase.
    forceload = models.IntegerField(db_column='forceLoad')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_RTM_BODY'
        unique_together = (('t_runtime_id_run', 't_equipment_id_equipment'),)


class TRuntime(models.Model):
    id_run = models.AutoField(primary_key=True)
    starting_date = models.DateTimeField(blank=True, null=True)
    job_name = models.CharField(max_length=45, blank=True, null=True)
    job_iteration = models.IntegerField(blank=True, null=True)
    owner = models.CharField(max_length=45)
    status = models.CharField(max_length=45)
    errcount = models.FloatField(db_column='errCount')  # Field name made lowercase.
    runcount = models.FloatField(db_column='runCount')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_RUNTIME'


class TScope(models.Model):
    id_scope = models.AutoField(primary_key=True)
    description = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'T_SCOPE'


class TSerial(models.Model):
    id_serial = models.AutoField(primary_key=True)
    inuse = models.IntegerField(db_column='inUse')  # Field name made lowercase.
    t_net_id_ip = models.ForeignKey(TNet, db_column='T_NET_id_ip')  # Field name made lowercase.
    port = models.IntegerField()
    t_equipment_id_equipment = models.ForeignKey(TEquipment, db_column='T_EQUIPMENT_id_equipment')  # Field name made lowercase.
    slot = models.IntegerField()
    subslot = models.IntegerField(blank=True, null=True)
    note = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_SERIAL'


class TSuites(models.Model):
    id_suite = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    owner = models.CharField(max_length=45)
    description = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_SUITES'


class TSuitesBody(models.Model):
    id_suites_body = models.AutoField(primary_key=True)
    t_suites_id_suite = models.ForeignKey(TSuites, db_column='T_SUITES_id_suite')  # Field name made lowercase.
    t_test_revs_id_testrev = models.ForeignKey('TTestRevs', db_column='T_TEST_REVS_id_TestRev')  # Field name made lowercase.
    tcorder = models.IntegerField(db_column='TCorder')  # Field name made lowercase.
    run_section = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = 'T_SUITES_BODY'


class TSwRel(models.Model):
    id_sw_rel = models.CharField(primary_key=True, max_length=45)
    sw_rel_name = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_SW_REL'


class TTest(models.Model):
    test_id = models.AutoField(primary_key=True)
    test_name = models.CharField(unique=True, max_length=255)
    test_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_TEST'


class TTestArea(models.Model):
    id_area = models.AutoField(primary_key=True)
    id_prod_rel = models.IntegerField(blank=True, null=True)
    jira_story = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_TEST_AREA'


class TTestCompatibility(models.Model):
    t_domain_id_domain = models.ForeignKey(TDomain, db_column='T_DOMAIN_id_domain')  # Field name made lowercase.
    t_test_revs_id_testrev = models.ForeignKey('TTestRevs', db_column='T_TEST_REVS_id_TestRev')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_TEST_COMPATIBILITY'


class TTestRevs(models.Model):
    id_testrev = models.AutoField(db_column='id_TestRev', primary_key=True)  # Field name made lowercase.
    t_test_test = models.ForeignKey(TTest, db_column='T_TEST_test_id')  # Field name made lowercase.
    revision = models.CharField(max_length=45)
    duration = models.IntegerField()
    metric = models.IntegerField()
    assignment = models.CharField(max_length=45)
    dependency = models.CharField(max_length=45)
    author = models.CharField(max_length=45)
    release_date = models.CharField(max_length=45)
    lab = models.CharField(max_length=45)
    description = models.CharField(max_length=45)
    topology = models.CharField(max_length=45)
    run_section = models.CharField(max_length=8)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'T_TEST_REVS'


class TTopology(models.Model):
    id_topology = models.AutoField(primary_key=True)
    t_scope_id_scope = models.ForeignKey(TScope, db_column='T_SCOPE_id_scope')  # Field name made lowercase.
    title = models.CharField(unique=True, max_length=45)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_TOPOLOGY'


class TTps(models.Model):
    id_tps = models.AutoField(primary_key=True)
    tps_reference = models.CharField(max_length=255)
    t_domain_id_domain = models.ForeignKey(TDomain, db_column='T_DOMAIN_id_domain')  # Field name made lowercase.
    t_test_revs_id_testrev = models.ForeignKey(TTestRevs, db_column='T_TEST_REVS_id_TestRev')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_TPS'


class TTpyEntity(models.Model):
    id_entity = models.AutoField(primary_key=True)
    t_topology_id_topology = models.ForeignKey(TTopology, db_column='T_TOPOLOGY_id_topology')  # Field name made lowercase.
    entityname = models.CharField(db_column='entityName', max_length=45)  # Field name made lowercase.
    elemname = models.CharField(db_column='elemName', max_length=45)  # Field name made lowercase.
    elemdescription = models.CharField(db_column='elemDescription', max_length=45, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'T_TPY_ENTITY'

class TEqptCredType(models.Model):
    idt_eqpt_cred_type = models.IntegerField(db_column='idT_EQPT_CRED_TYPE', primary_key=True)  # Field name made lowercase.
    cr_type = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'T_EQPT_CRED_TYPE'



class TEqptCred(models.Model):
    cred_id = models.IntegerField(primary_key=True)
    t_eqpt_cred_type_id_cred_type = models.ForeignKey('TEqptCredType', db_column='T_EQPT_CRED_TYPE_id_cred_type')  # Field name made lowercase.
    t_equipment_id_equipment = models.ForeignKey('TEquipment', db_column='T_EQUIPMENT_id_equipment', blank=True, null=True)  # Field name made lowercase.
    usr = models.CharField(max_length=45, blank=True, null=True)
    pwd = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'T_EQPT_CRED'

