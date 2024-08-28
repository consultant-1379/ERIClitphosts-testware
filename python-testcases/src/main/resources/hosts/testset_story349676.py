"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Jun 2019
@author:    Karen Flannery
@summary:   TORF-349676 As a LITP engineer, I need to update IPv6
            aliases so that they can be successfully written to
            /etc/hosts
"""
from litp_generic_test import GenericTest, attr
import test_constants as const
import hosts_test_data as data


class Story349676(GenericTest):
    """
       As a LITP engineer, I need to update IPv6 aliases so that they
       can be successfully written to /etc/hosts

    """

    def setUp(self):
        """
            Runs before every single test
        """
        super(Story349676, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = [self.ms_node] + self.peer_nodes
        self.cluster_path = self.find(self.ms_node, "/deployments",
                                      "collection-of-cluster-base")
        self.cluster_config_path = self.find(self.ms_node,
             self.cluster_path[0], "collection-of-cluster-config")
        self.alias_cluster_config_path = '{0}/alias_config'.format(
            self.cluster_config_path[0])
        self.alias_ms_config_path = self.find(
            self.ms_node, "/ms", "alias-node-config")[0]
        self.alias_ms_path = "{0}/{1}".format(self.alias_ms_config_path,
                                              "aliases")
        self.cluster_alias_item_id = "clusterAlias"
        self.ms_alias_item_id = "msAlias"
        self.alias_name = "story349676-service"
        self.ipv6_address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        self.ipv6_address_update = "2001:0db8:85a3:0000:0000:8a2e:0370:9874"
        self.ipv6_prefix = "64"
        self.ipv6_prefix_update = "128"

        for node in self.all_nodes:
            self.backup_file(node, const.ETC_HOSTS)

    def tearDown(self):
        """
            Runs after every single test
        """
        super(Story349676, self).tearDown()

    def check_host_file(self, ip_address, expected_value, node_alias=""):
        """
        Description:
             Checks the /etc/hosts file(s) for a specified alias IP and
             alias name on the specified node.
        Args:
            ip_address (str): The IP address of the alias to search for
                              in the file
            expected_value (str): The expected number of times the IP
                                  is matched in the file
            node_alias (str): (Optional) To check only on a particular
                            node, pass in the hostname of the node.
                            Default is an empty string and therefore
                            will check all peer nodes
        """

        nodes = self.all_nodes
        if node_alias in self.all_nodes:
            nodes = [node_alias]

        cat_hosts_ipv6_alias_cmd = "{0} {1} {2} | {3} '{{print $1}}'".\
            format(const.GREP_PATH, self.alias_name, const.ETC_HOSTS,
                   const.AWK_PATH)

        cat_hosts_ipv6address_count_cmd = "{0} {1} {2} | wc -l".format(
            const.GREP_PATH, ip_address, const.ETC_HOSTS)

        for node in nodes:
            ipaddress = self.run_command(node, cat_hosts_ipv6_alias_cmd,
                                         su_root=True, default_asserts=True)[0]

            count = self.run_command(node, cat_hosts_ipv6address_count_cmd,
                                     su_root=True, default_asserts=True)[0]
            self.assertEqual(expected_value, count[0],
                             "Number of aliases in host file is not as "
                             "expected")

            if expected_value != "0":
                self.assertEqual(ip_address, ipaddress[0],
                    "Expected IP address is not the same as actual IP address")

    def create_alias(self, url, alias, address):
        """
        Description:
            Create alias in LITP model.
        Args:
            url (str): LITP path to create alias
            alias (str): Name of the alias for the LITP model url.
            address (str) : Value for the IP address property of the
                            alias.
        Return: link_url(str): LITP path to created alias
        """
        link_url = "{0}/aliases/{1}".format(url, alias)
        props = "address={0} alias_names={1}".format(address, self.alias_name)

        self.execute_cli_create_cmd(
            self.ms_node, link_url, "alias", props)

        return link_url

    def assert_alias_props_model(self, alias_cluster_path, ipv6address,
                                 ipv6prefix):
        """
        Description:
            Assert alias properties in LITP model
        Args:
            alias_cluster_path (str): LITP path to alias
            ipv6address (str): IP address of the alias
            ipv6prefix (str): IP address prefix of the alias
        """

        alias_cluster_props_in_model = self.get_props_from_url(self.ms_node,
            "{0}/{1}".format(alias_cluster_path, self.cluster_alias_item_id))
        alias_ms_props_in_model = self.get_props_from_url(self.ms_node,
            "{0}/{1}".format(self.alias_ms_path, self.ms_alias_item_id))

        values_to_compare = {
            "alias_names": self.alias_name,
            "address": "{0}/{1}".format(ipv6address, ipv6prefix)}

        for model_value, expected_value in values_to_compare.iteritems():
            self.assertEqual(alias_cluster_props_in_model["{0}".format(
                model_value)], expected_value, "Cluster level alias properties"
                                               " are not as expected")
            self.assertEqual(alias_ms_props_in_model["{0}".format
                             (model_value)], expected_value, "MS level alias"
                                            " properties are not as expected")

        address_values_to_compare = [alias_cluster_props_in_model["address"],
                                     alias_ms_props_in_model["address"]]
        for value in address_values_to_compare:
            self.assertNotEqual(value, ipv6address, "IP address in model is "
                                        "the same as IP address in host file")

    @attr('all', 'revert', 'story349676', 'story349676_tc01')
    def test_01_p_create_update_remove_alias_ipv6_address_with_prefix(self):
        """
        @tms_id: torf_349676_tc01
        @tms_requirements_id: TORF-349676
        @tms_title: test_01_p_create_update_remove_alias
        @tms_description: Test creates, updates and removes an alias
         with IPv6 address including prefix
        @tms_test_steps:
            @step: Create cluster-level and ms-level alias items
             Create and run plan
            @result: Plan executes successfully. Alias items are
             created in LITP model
            @step: Check /etc/hosts file is updated with ipv6 address
             without prefix and model contains ipv6 address with prefix
            @result: /etc/hosts file is updated with ipv6 address
             without prefix and model contains ipv6 address with prefix
            @step: Update alias address prefix ONLY. Execute create
             plan and assert DoNothingPlanError
            @result: Create plan fails with DoNothingPlanError. Alias
             address prefix is updated in LITP model
            @step: Check /etc/hosts file is unchanged and model
             contains ipv6 address with updated prefix
            @result: /etc/hosts file is unchanged and model contains
             ipv6 address with updated prefix
            @step: Update alias address. Create and run plan
            @result: Plan executes successfully. Alias items are
             updated in the LITP model
            @step: Check /etc/hosts file is updated with ipv6 address
             without prefix and model contains ipv6 address with prefix
            @result: /etc/hosts file is updated with ipv6 address
             without prefix and model contains updated ipv6 address
             with prefix
            @step: Remove alias and alias_config. Create and run plan
            @result: Plan executes successfully. Alias items are
             removed from LITP model
            @step: Check entries have been removed from /etc/hosts file
            @result: Entries have been removed from /etc/hosts file
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        self.log("info", "# 1. Create a cluster-level and ms-level alias item."
                         " Create and run plan")
        self.execute_cli_create_cmd(self.ms_node, "{0}/{1}".format(
            self.cluster_config_path[0], "alias_config"),
                                    "alias-cluster-config")

        create_alias_details = {self.alias_cluster_config_path: self.
            cluster_alias_item_id, self.alias_ms_config_path: self.
            ms_alias_item_id}

        for path, item_id in create_alias_details.iteritems():
            self.create_alias(path, item_id, "{0}/{1}".format(
                self.ipv6_address, self.ipv6_prefix))

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 10)

        self.log("info", "# 2. Check /etc/hosts file is updated with ipv6 "
                         "address without prefix and model contains "
                         "ipv6 address with prefix")
        self.check_host_file(self.ipv6_address, "1")
        self.check_host_file("{0}/{1}".format(self.ipv6_address,
                                              self.ipv6_prefix), "0")

        alias_cluster_path = "{0}/{1}".format(self.alias_cluster_config_path,
                                              "aliases")
        self.assert_alias_props_model(alias_cluster_path, self.ipv6_address,
                                      self.ipv6_prefix)

        self.log("info", "# 3. Update alias address prefix ONLY. "
                         "Execute create plan and assert DoNothingPlanError")
        alias_details = {alias_cluster_path: self.cluster_alias_item_id,
                         self.alias_ms_path: self.ms_alias_item_id}
        for path, item_id in alias_details.iteritems():
            self.execute_cli_update_cmd(self.ms_node, "{0}/{1}".format(path,
                   item_id), "address={0}/{1}".format(self.ipv6_address,
                                                      self.ipv6_prefix_update))

        do_nothing_plan_error = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertEqual(do_nothing_plan_error[1][0], data.
                         FAILED_PLAN_ERROR_MSG, "Error message is not as "
                                                "expected")

        self.log("info", "# 4. Check /etc/hosts file is unchanged and model "
                         "contains ipv6 address with updated prefix")
        self.check_host_file(self.ipv6_address, "1")
        self.check_host_file("{0}/{1}".format(self.ipv6_address,
                                              self.ipv6_prefix_update), "0")
        self.assert_alias_props_model(alias_cluster_path, self.ipv6_address,
                                      self.ipv6_prefix_update)

        self.log("info", "# 5. Update alias address. Create and run plan")
        for path, item_id in alias_details.iteritems():
            self.execute_cli_update_cmd(self.ms_node, "{0}/{1}".format(path,
                item_id), "address={0}/{1}".format(self.ipv6_address_update,
                                                self.ipv6_prefix))
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 10)

        self.log("info", "# 6. Check /etc/hosts file is updated with ipv6 "
            "address without prefix and model contains ipv6 address with "
                         "prefix")
        self.check_host_file(self.ipv6_address_update, "1")
        self.check_host_file("{0}/{1}".format(self.ipv6_address_update,
                                              self.ipv6_prefix), "0")
        self.assert_alias_props_model(alias_cluster_path,
                                self.ipv6_address_update, self.ipv6_prefix)

        self.log("info", "# 7. Remove alias and alias_config. "
                         "Create and run plan")
        for path, item_id in alias_details.iteritems():
            self.execute_cli_remove_cmd(self.ms_node, "{0}/{1}".format(path,
                                                    item_id))
        self.execute_cli_remove_cmd(self.ms_node, self.
                                    alias_cluster_config_path)
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 10)

        self.log("info", "# 8. Check entries have been removed from "
                         "/etc/hosts file")
        self.check_host_file(self.ipv6_address_update, "0")
        self.check_host_file("{0}/{1}".format(self.ipv6_address_update,
                                              self.ipv6_prefix), "0")
