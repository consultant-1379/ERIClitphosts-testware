"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2015; Refactored April 2018
@author:    Maria; Aisling Stafford
@summary:   As a LITP User, I want the XSD validation to allow
            for property annotation, so that I can use external
            tools to extract semantic information about these properties
            Agile: STORY LITPCDS-7534
"""

from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
import hosts_test_data as hosts_data


class Story7534(GenericTest):
    """
       As a LITP User, I want the XSD validation to allow
       for property annotation, so that I can use external
       tools to extract semantic information about these properties
    """

    def setUp(self):
        """
        Runs before every single test
        """

        super(Story7534, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.xml = XMLUtils()

        self.cluster_path = self.find_children_of_collect(
            self.ms_node, "/deployments", "cluster")[0]

        self.cluster_config_path = self.find(self.ms_node, self.cluster_path,
                                             "collection-of-cluster-config")[0]

        self.alias_cluster_config_path = '{0}/alias_config'.format(
            self.cluster_config_path)

        self.alias_path = '{0}/aliases'.format(self.alias_cluster_config_path)

        self.new_name_value = "%%SITE_SPECIFIC%%"
        self.xml_file = "/tmp/test1.xml"

    def tearDown(self):
        """
         Runs after every single test
        """
        super(Story7534, self).tearDown()

    def create_alias(self, alias_data):
        """
        Description:
            Creates aliases in the litp model

        Args:
            alias_data (dict): information about the alias to be created
            i.e. props, name of alias

        Returns:
            str. Path to created alias
        """
        alias_config = self.find(self.ms_node,
                                 self.cluster_config_path,
                                 "alias-cluster-config",
                                 assert_not_empty=False)
        if not alias_config:
            self.execute_cli_create_cmd(self.ms_node,
                                        self.alias_cluster_config_path,
                                        "alias-cluster-config")

        alias_path = '{0}/aliases/{1}'.format(self.alias_cluster_config_path,
                                              alias_data["NAME"])

        alias_props = ""
        for prop_name, prop_value in alias_data["PROPS"].iteritems():
            alias_props += '{0}="{1}" '.format(prop_name, prop_value)

        self.execute_cli_create_cmd(self.ms_node, alias_path, "alias",
                                    alias_props)

        return alias_path

    @attr('all', 'revert', 'story7534', 'story7534_tc09')
    def test_09_n_load_annotated_value_with_accept_all_regex(self):
        """
        @tms_id: litpcds_7534_tc09
        @tms_requirements_id: LITPCDS-7534
        @tms_title: export and load of a service alias
        @tms_description: This tests export and load of a service alias
        @tms_test_steps:
            @step: Create cluster-level service alias
            @result: Service alias created
            @step: Export the service alias
            @result: alias is exported
            @step: Remove the service alias
            @result: Service alias is removed
            @step: Load the xml into an object using the xml utilities
            @result: xml is loaded
            @step: Search and update the address property
            @result: Property is updated
            @step: Convert the object back to XML
            @result: Object is converted back to XML
            @step: Output the xml into a file on the MS
            @result: xml outputted to a file
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        self.log("info", "# 1. Create, export and remove cluster-level "
                         "service alias")
        alias = self.create_alias(hosts_data.EXPORT_ALIAS)

        stdout, _, _ = self.execute_cli_export_cmd(self.ms_node, alias)
        self.assertNotEqual([], stdout)

        self.execute_cli_remove_cmd(self.ms_node, alias)

        self.log("info", "# 2. Load the XML into an object. Search and update "
                         "the address property")
        xml_object = self.xml.load_xml_dataobject(stdout)

        name_found = False
        for child in xml_object:
            if child.tag == 'address':
                child.text = self.new_name_value
                name_found = True
                break

        self.assertTrue(name_found,
                        "Could not find 'address' property in xml object")

        self.log("info", "# 3. Convert the object back to XML and output the "
                         "XML into a file on the MS")
        xml_string = self.xml.output_xml_dataobject(xml_object)

        self.assertTrue(self.create_file_on_node(self.ms_node,
                                                 self.xml_file,
                                                 xml_string.split("\n")),
                        "Failed to output xml to a file on the MS")
