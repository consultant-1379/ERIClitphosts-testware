"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2014; Refactored April 2018
@author:    Maria/Priyanka/John L; Aisling Stafford
@summary:   As a site engineer I want to create a service alias
            for external network accessible services so
            I can configure my nodes to access the service (Service aliasing)
            Agile: STORY LITPCDS-54
"""
from litp_generic_test import GenericTest, attr
import test_constants as const
import hosts_test_data as data


class Story54(GenericTest):
    """
       As a site engineer I want to create a service alias
       for external network accessible services so
       I can configure my nodes to access the service (Service aliasing)
    """

    def setUp(self):
        """
            Runs before every single test
        """
        super(Story54, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.node_urls = self.find(self.ms_node, '/deployments', 'node')

        self.cluster_path = self.find_children_of_collect(
            self.ms_node, "/deployments", "cluster")[0]
        self.cluster_config_path = self.find(self.ms_node, self.cluster_path,
                                             "collection-of-cluster-config")[0]
        self.alias_cluster_config_path = '{0}/alias_config'.format(
            self.cluster_config_path)

        self.ms_config_path = self.find(
            self.ms_node, "/ms", "collection-of-node-config")[0]
        self.node1_config_path = self.find(
            self.ms_node, self.node_urls[0], "collection-of-node-config")[0]
        self.node2_config_path = self.find(
            self.ms_node, self.node_urls[1], "collection-of-node-config")[0]

        self.alias_node1_config_path = '{0}/alias_node_config'.format(
                                                self.node1_config_path)
        self.alias_node2_config_path = '{0}/alias_node_config'.format(
                                                self.node2_config_path)

        for node in self.peer_nodes:
            self.backup_file(node, const.ETC_HOSTS)

    def tearDown(self):
        """
            Runs after every single test
        """
        super(Story54, self).tearDown()

    def check_etc_hosts_file(self, ip_address, expected_value, alias_names,
                             node_alias=""):
        """
        Description:
             Checks the /etc/hosts file(s) for a specified alias IP and
             alias name on the specified node.

        Args:
            ip_address (str): The IP address of the alias to search for in the
                            file

            expected_value (str): The expected number of times the IP is
                                  matched in the file.

            alias_names (list) : The alias name of the alias to search for in
                                 the file.

        Kwargs:
            node_alias (str): To check only on a particular node, pass in
                              the hostname of the node. Default is an
                              empty string and therefore will check all peer
                              nodes.
        """
        nodes = self.peer_nodes
        if node_alias in self.peer_nodes:
            nodes = [node_alias]

        cmd = "{0} {1} {2} | wc -l".format(const.GREP_PATH, ip_address,
                                           const.ETC_HOSTS)

        for node in nodes:
            stdout, _, _ = self.run_command(node, cmd, su_root=True,
                                            default_asserts=True)
            self.assertEqual(expected_value, stdout[0])

        for node in nodes:
            for name in alias_names:
                cmd = "{0} {1} {2}".format(const.GREP_PATH, name,
                                           const.ETC_HOSTS)
                stdout, _, _ = self.run_command(node, cmd,
                                                default_asserts=True)
                for line in stdout:
                    ip_and_aliases, _, _ = line.partition('#')
                    address = ip_and_aliases.split()[0:1][0]
                    self.assertTrue(address == ip_address)

    def ensure_alias_config_exists(self, alias_data, node_config=False):
        """
        Description:
            Checks if alias cluster/node config exists and, if
            not, creates it and returns the path to it.

        Args:
            alias_data (dict): dictionary of information about alias
                               to be created

        Kwargs:
            node_config (bool): If True, will check for an alias-node-config
                               item under the node in the given dictionary.
                               If False, will check for an alias-cluster-config
                               item. If the item being searched for does not
                               exist, it will be created.
                               Default value is False.
        Returns:
            str. Path to (created) alias cluster/node config.
        """
        if node_config:
            config_path = alias_data["PATH"]
            alias_path = alias_data["ALIAS_PATH"]
            resource = "alias-node-config"

        else:
            config_path = self.cluster_config_path
            alias_path = self.alias_cluster_config_path
            resource = "alias-cluster-config"

        alias_config = self.find(self.ms_node,
                                 config_path,
                                 resource,
                                 assert_not_empty=False)

        if not alias_config:
            self.execute_cli_create_cmd(self.ms_node, alias_path, resource)
            alias_config = self.find(self.ms_node,
                                     config_path,
                                     resource,
                                     assert_not_empty=False)
        return alias_config[0]

    def create_update_alias(self, alias_data, update=False, node_alias=False):
        """
        Description:
            Creates/updates aliases in the LITP model

        Args:
            alias_data (dict): Information about the alias to be created/
            updated. Ex. props, name of alias


        Kwargs:
            update (bool): If True, will update the specified alias. If False,
                           will create the alias. Default is False

            node_alias (bool): If True, creates a node alias. If False,
                               creates a cluster alias. Default is False.
        Returns:
            str. Path to created/updated alias
        """
        alias_config = self.ensure_alias_config_exists(alias_data, node_alias)

        alias_path = '{0}/aliases/{1}'.format(alias_config,
                                              alias_data["NAME"])

        alias_props = ""
        for prop_name, prop_value in alias_data["PROPS"].iteritems():
            alias_props += '{0}="{1}" '.format(prop_name, prop_value)

        if update:
            self.execute_cli_update_cmd(self.ms_node, alias_path, alias_props)
        else:
            self.execute_cli_create_cmd(self.ms_node, alias_path, "alias",
                                        alias_props)

        return alias_path

    def _create_alias(self, alias, alias_names, address):
        """
        Description:
            Create alias in LITP model.
        Args:
            alias (str): Name of the alias for the LITP model url.
            alias_names (str): Values for the alias_names property of the
                               alias.
            address (str) : Value for the IP address property of the alias.
        """
        link_url = self.alias_cluster_config_path + "/aliases/{0}".format(
            alias)
        props = "address={0} alias_names={1}".format(address, alias_names)

        self.execute_cli_create_cmd(
            self.ms_node, link_url, "alias", props)

        return link_url

    @attr('all', 'revert', 'story54', 'story54_tc01', 'cdb_priority1')
    def test_01_p_create_update_remove_alias(self):
        """
        @tms_id: litpcds_54_tc01
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_01_p_create_update_remove_alias
        @tms_description: Test creates, updates and removes a service alias.
        @tms_test_steps:
            @step: Create a cluster-level alias item.
            @result: Alias item created in the LITP model.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts file contains the alias.
            @result: /etc/hosts file contains the alias.
            @step: Update alias item with a new IP address.
            @result: Alias updated.
            @step: Create another alias item with the same IP address and
                   different alias_names.
            @result: Alias item created in the LITP model.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts file contains expected aliases.
            @result: /etc/hosts file contains the expected aliases.
            @step: Remove an alias item from LITP model.
            @result: Alias removed from LITP model.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check alias removed from /etc/hosts file.
            @result: /etc/hosts file has expected contents.
            @step: Update existing alias item to have comma separated list in
                   alias_names.
            @result: Alias item created in the LITP model.
            @step: Create new alias with specified IPv6.
            @result: Alias item updated in the LITP model.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts file contains expected aliases.
            @result: /etc/hosts file contains expected aliases.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        self.log("info", "# 1. Create a cluster-level alias item.")
        self.execute_cli_create_cmd(self.ms_node,
                                    self.alias_cluster_config_path,
                                    "alias-cluster-config")

        svn_alias = self._create_alias(
            "svn", "svn-service", "122.122.54.51")

        self.log("info", "# 2. Create and Run plan. Check /etc/hosts file "
                         "contains the alias.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.check_etc_hosts_file("122.122.54.51", "1", ["svn-service"])

        self.log("info", "# 3. Update alias item with a new IP address."
                         "Create another alias item with the same IP address"
                         "and alias_names as the original.")

        props = "address=122.122.54.151"
        self.execute_cli_update_cmd(self.ms_node, svn_alias, props)

        self.log("info", "# 4. Create another alias item with the same IP "
                         "address and different alias_names.")
        apache_alias = self._create_alias(
            "apache", "apache-service", "122.122.54.151")

        self.log("info", "# 5. Create and Run plan. Check /etc/hosts file "
                         "contains expected aliases.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.check_etc_hosts_file("122.122.54.151", "2",
                                  ["apache-service", "svn-service"])

        self.log("info", "# 6. Remove an alias item from LITP model.")
        self.execute_cli_remove_cmd(self.ms_node, apache_alias)

        self.log("info", "# 7. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "8. Check alias removed from /etc/hosts file.")
        self.check_etc_hosts_file("122.122.54.151", "1", [])

        self.log("info", "# 9. Update existing alias item to have comma "
                         "separated list in alias_names. "
                         "Create new alias with specified IPv6.")

        props = "alias_names='apache-service,svn-service'"
        self.execute_cli_update_cmd(self.ms_node, svn_alias, props)

        self._create_alias("aliasipv6", "ipv6-service",
                           "fe80::a00:27ff:febc:c8e1")

        self.log("info", "# 10. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "# 11. Check /etc/hosts file contains expected "
                         "aliases ")
        alias_names = "apache-service,svn-service".split(',')
        self.check_etc_hosts_file("122.122.54.151", "1", alias_names)

        self.check_etc_hosts_file("fe80::a00:27ff:febc:c8e1", "1",
                                  ["ipv6-service"])

    @attr('all', 'revert', 'story54', 'story54_tc02')
    def test_02_p_ip_with_multiple_names(self):
        """
        @tms_id: litpcds_54_tc02
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_02_p_ip_with_multiple_names
        @tms_description: Test create alias with unique ip and multiple names
        @tms_test_steps:
            @step: Create two aliases at cluster-level with the same IP
                   address.
            @result: Aliases created.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts file for two aliases with the same IP
                   address.
            @result: Expected aliases present in /etc/hosts file on each peer
                    node.
            @step: Remove aliases and alias cluster config.
            @result: Aliases and alias_config removed from nodes in cluster.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts file contains no aliases.
            @result: No aliases present in /etc/hosts file on each peer
                     node.
            @step: Create cluster alias with two alias names and one IP.
            @result: Alias created.
            @step: Create and Run plan.
            @result: Plans runs to completion successfully.
            @step: Check /etc/hosts file to verify alias with two names and
                   one IP is present.
            @result: /etc/hosts contains alias.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        self.log("info", "1. Create two aliases at cluster-level with the"
                         "same IP address")
        mail_alias = self.create_update_alias(data.MAIL_ALIAS_4)
        web_alias = self.create_update_alias(data.WEB_ALIAS_5)

        self.log("info", "2. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "3. Check /etc/hosts file for two aliases with the "
                         "same IP address.")
        address = data.WEB_ALIAS_5["PROPS"]["address"]
        alias_names = [data.MAIL_ALIAS_4["PROPS"]["alias_names"],
                       data.WEB_ALIAS_5["PROPS"]["alias_names"]]
        self.check_etc_hosts_file(address, "2", alias_names)

        self.log("info", "4. Remove aliases and cluster config.")
        self.execute_cli_remove_cmd(self.ms_node, mail_alias)
        self.execute_cli_remove_cmd(self.ms_node, web_alias)
        self.execute_cli_remove_cmd(self.ms_node,
                                    self.alias_cluster_config_path)

        self.log("info", "5. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "6. Check /etc/hosts file contains no aliases.")
        address = data.WEB_ALIAS_5["PROPS"]["address"]
        alias_names = []
        self.check_etc_hosts_file(address, "0", alias_names)

        self.log("info", "7. Create cluster alias with two alias names and "
                         "one IP. ")
        self.create_update_alias(data.COMMS_ALIAS_6)

        self.log("info", "8. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "9. Check /etc/hosts file to verify alias with two "
                         "names and one IP is present.")
        address = data.COMMS_ALIAS_6["PROPS"]["address"]
        alias_names = data.COMMS_ALIAS_6["PROPS"]["alias_names"].split(',')
        self.check_etc_hosts_file(address, "1", alias_names)

    # @attr('pre-reg', 'revert', 'story54', 'story54_tc03')
    def obsolete_03_n_conflicting_ips_cli(self):
        """
        Test converted to test_03_n_conflicting_ips_cli.at in hosts.
        #tms_id: litpcds_54_tc03
        #tms_requirements_id: LITPCDS-54
        #tms_title: test_03_n_conflicting_ips_cli
        #tms_description: Test try to creates a aliases with Duplicate name
        #tms_test_steps:
            #step: Create 2 aliases items, a duplicate name on different rows
            #result: Create plan fails with correct validation
            #step: Update both alias items to have twin alias names,
                a duplicate in each name
            #result: Create plan fails with correct validation
        #tms_test_precondition:NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story54', 'story54_tc04')
    def  obsolete_04_n_invalid_scenarios(self):
        """
        Test converted to test_04_n_invalid_scenarios.at in
        hosts/ats/testset_story54
        @tms_id: litpcds_54_tc04
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_04_n_invalid_scenarios
        @tms_description: Test creates alias with invalid scenarios and
            loads at invalid place in the model.
        @tms_test_steps:
            @step: Create a service alias with invalid url address
            @result: Create plan fails with correct validation
            @step: Create service alias with missing required property
            @result: Create plan fails with correct validation
            @step: Create service alias with an invalid IP
            @result: Create plan fails with correct validation
            @step: Create alias with invalid type
            @result: Create plan fails with correct validation
            @step: Create alias item with unsupported alias names
            @result: Create plan fails with correct validation
            @step: Create alias config without an alias item
            @result: Create plan fails with correct validation
            @step: Create alias item with restricted alias name hostname
            @result: Create plan fails with correct validation
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

    @attr('all', 'revert', 'story54', 'story54_tc05')
    def test_05_n_manual_file_update(self):
        """
        @tms_id: litpcds_54_tc05
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_05_n_manual_file_update
        @tms_description: test litp rule enforced when there is an existing
            manually created rule
        @tms_test_steps:
            @step: Add alias manually to peer nodes /etc/hosts file. Add
                    alias with same IP as manual alias.
            @result: Aliases added.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts to ensure created aliases are present.
            @result: Aliases present.
            @step: Remove the manual alias from all peer nodes.
            @result: Alias removed.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        self.log("info", "# 1. Add alias manually to peer nodes. Add alias "
                         "with same ip as manual alias.")
        cmd = "{0} '{1} {2} # manually added by {3}' >> {4}".format(
            const.ECHO_PATH,
            data.MANUAL_ALIAS["ADDRESS"],
            data.MANUAL_ALIAS["NAME"],
            "test_05_n_manual_file_update",
            const.ETC_HOSTS)

        for node in self.peer_nodes:
            _, _, rc = self.run_command(node, cmd, su_root=True)
            self.assertEquals(0, rc)

        self.create_update_alias(data.CRABLOUIE_ALIAS_7)

        self.log("info", "# 2. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "# 3. Check /etc/hosts to ensure created aliases "
                         "are present.")
        address = data.CRABLOUIE_ALIAS_7["PROPS"]["address"]
        alias_names = [data.CRABLOUIE_ALIAS_7["PROPS"]["alias_names"]]

        self.check_etc_hosts_file(address, "2", alias_names)

        self.log("info", "# 4. Remove the manual alias from all peer nodes.")
        cmd = "{0} -i '/{1}/d' {2}".format(const.SED_PATH,
                                           data.MANUAL_ALIAS["NAME"],
                                           const.ETC_HOSTS)
        for node in self.peer_nodes:
            _, _, rc = self.run_command(node, cmd, su_root=True)
            self.assertEquals(0, rc)

    @attr('all', 'revert', 'story54', 'story54_tc06', 'cdb_tmp')
    def test_06_p_service_alias_export_load_xml(self):
        """
        @tms_id: litpcds_54_tc06
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_06_p_service_alias_export_load_xml
        @tms_description: This test xml export and load of a service alias.
        @tms_test_steps:
            @step: create a service alias of the type alias
            @result: alias item created
            @step: export the service alias
            @result: alias is exported to a file
            @step: remove the service alias
            @result: alias is removed from the litp model
            @step: litp xml load the service alias into model
            @result: alias item created in litp model
            @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        self.execute_cli_create_cmd(self.ms_node,
                                    self.alias_cluster_config_path,
                                    "alias-cluster-config")
        # Create service alias
        export_alias = self._create_alias(
            "exportalias", "exportalias", "122.122.54.56")

        # Export the service alias
        xml_file = "expected_06_story54.xml"
        self.execute_cli_export_cmd(self.ms_node, export_alias, xml_file)

        # Delete created alias
        self.execute_cli_remove_cmd(self.ms_node, export_alias)

        items_path = self.find(
            self.ms_node, "/deployments", "alias", False)[0]

        # Load the service alias
        self.execute_cli_load_cmd(self.ms_node, items_path, xml_file)

        # Delete created alias
        self.execute_cli_remove_cmd(self.ms_node, export_alias)

    # attr('pre-reg', 'revert', 'story54', 'story54_tc07')
    def obsolete_07_p_create_alias_at_node_level(self):
        """
        Test merged with test_08_p_create_two_node_level_aliases.
        #tms_id: litpcds_54_tc07
        #tms_requirements_id: LITPCDS-54
        #tms_title: test_07_p_create_alias_at_node_level
        #tms_description: Test creates node-level alias and removes it.
        #tms_test_steps:
            #step: Create alias at node level.
            #result: Alias created.
            #step: Create and Run plan.
            #result: Plan runs to completion successfully.
            #step: Check etc/hosts to ensure the alias is present on the
                   specified node.
            #result: Alias is present.
            #step: Remove Node Config.
            #result: Config removed.
            #step: Create and Run plan.
            #result: Plan runs to completion successfully.
            #step: Check etc/hosts to ensure there are no aliases present.
            #result: There are no aliases present.
        #tms_test_precondition:NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story54', 'story54_tc08')
    def test_08_p_create_two_node_level_aliases(self):
        """
        @tms_id: litpcds_54_tc08
        @tms_requirements_id: LITPCDS-54
        @tms_title: test_08_p_create_two_node_level_aliases
        @tms_description: Test creates two node-level aliases and removes one
                          of them so covers litpcds_54_tc07
        @tms_test_steps:
            @step: Create two node-level aliases with the same alias name;
                   one on each peer node.
            @result: Aliases created.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check /etc/hosts to ensure created aliases are present.
            @result: Aliases are present.
            @step: Remove Node Config.
            @result: Config removed.
            @step: Create and Run plan.
            @result: Plan runs to completion successfully.
            @step: Check etc/hosts to ensure there are no aliases present.
            @result: There are no aliases present.
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """

        spaghetti = data.SPAGHETTI_ALIAS_8
        spaghetti["NODE"] = self.peer_nodes[0]
        spaghetti["PATH"] = self.node1_config_path
        spaghetti["ALIAS_PATH"] = self.alias_node1_config_path

        linguini = data.LINGUINI_ALIAS_9
        linguini["NODE"] = self.peer_nodes[1]
        linguini["PATH"] = self.node2_config_path
        linguini["ALIAS_PATH"] = self.alias_node2_config_path
        node_aliases = [spaghetti, linguini]

        self.log("info", "1. Create two node-level aliases with the same "
                         "alias name; one on each peer node.")
        for alias in node_aliases:
            self.create_update_alias(alias, node_alias=True)

        self.log("info", "2. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "3. Check /etc/hosts to ensure created aliases are "
                         "present.")
        address = data.SPAGHETTI_ALIAS_8["PROPS"]["address"]
        alias_names = [data.SPAGHETTI_ALIAS_8["PROPS"]["alias_names"]]
        self.check_etc_hosts_file(address, "1", alias_names,
                                  node_alias=spaghetti["NODE"])

        address = data.LINGUINI_ALIAS_9["PROPS"]["address"]
        alias_names = [data.LINGUINI_ALIAS_9["PROPS"]["alias_names"]]
        self.check_etc_hosts_file(address, "1", alias_names,
                                  node_alias=linguini["NODE"])

        self.log("info", "4. Remove Node Config.")
        self.execute_cli_remove_cmd(self.ms_node, spaghetti["ALIAS_PATH"])

        self.log("info", "5. Create and Run plan.")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log("info", "6. Check etc/hosts to ensure there are no aliases "
                         "present.")
        alias_names = []
        self.check_etc_hosts_file(address, "0", alias_names,
                                  node_alias=spaghetti["NODE"])
