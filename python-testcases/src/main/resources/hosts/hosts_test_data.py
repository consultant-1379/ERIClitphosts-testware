"""
Data file for Hosts tests
"""

####### testset_story54 ##################

######## test_01_p_create_update_remove_alias ########

SVN_ALIAS_1_ERROR_MSG = 'ValidationError in property: "alias_name"    ' \
                        'Create plan failed: Duplicate alias for ' \
                        'svn-service found at {0}, {1}'

######### test_02_p_ip_with_multiple_names ########

MAIL_ALIAS_4 = {"NAME": "mail",
                "PROPS": {"address": "122.122.54.52",
                          "alias_names": "mail-service"}}

WEB_ALIAS_5 = {"NAME": "web",
               "PROPS": {"address": "122.122.54.52",
                         "alias_names": "web-service"}}

COMMS_ALIAS_6 = {"NAME": "comms",
                 "PROPS": {"address": "122.122.54.52",
                           "alias_names": "mail-service,web-service"},
                 "HOSTS_FILE_CHECK": "mail-service\tweb-service"}

######### test_05_n_manual_file_update ########

MANUAL_ALIAS = {"NAME": "caesar-salad",
                "ADDRESS": "122.122.54.55"}

CRABLOUIE_ALIAS_7 = {"NAME": "crablouie",
                     "PROPS": {"address": "122.122.54.55",
                               "alias_names": "crablouie"}}

######### test_07_p_create_alias_at_node_level ########

REPAIR_ALIAS_10 = {"NAME": "repair",
                   "PROPS": {"address": "122.122.54.57",
                             "alias_names": "repair-service"}}

####### test_08_p_create_two_node_level_aliases ########

SPAGHETTI_ALIAS_8 = {"NAME": "spaghetti",
                     "PROPS": {"address": "122.122.54.58",
                               "alias_names": "pasta-service"}}

LINGUINI_ALIAS_9 = {"NAME": "linguini",
                    "PROPS": {"address": "122.122.54.158",
                              "alias_names": "pasta-service"}}

########## testset_story7534 #####################
###### test_09_n_load_annotated_value_with_accept_all_regex #######

EXPORT_ALIAS = {"NAME": "exportalias",
                "PROPS": {"address": "122.122.54.56",
                          "alias_names": "exportalias"}}

####### testset_story349676 ##################

######## test_01_p_create_update_remove_alias_ipv6_address_with_suffix ########
FAILED_PLAN_ERROR_MSG = "DoNothingPlanError    " \
                        "Create plan failed: no tasks were generated"
