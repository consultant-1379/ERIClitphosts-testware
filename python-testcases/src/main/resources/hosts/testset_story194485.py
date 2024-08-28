"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     June 2017; Refactored April 2018
@author:    Laura Forbes, Pat Bohan; Aisling Stafford
@summary:   TORF-194485
            As a LITP user I want the node entry of a node which is being
            removed from the model to also be removed from the /etc/hosts
            file of all remaining nodes in the deployment
"""
from litp_generic_test import GenericTest, attr
import test_constants as const


class Story194485(GenericTest):
    """
        As a LITP user I want the node entry of a node which is being
        removed from the model to also be removed from the /etc/hosts
        file of all remaining nodes in the deployment
    """

    def setUp(self):
        """ Runs before every single test """
        super(Story194485, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.removed_node = self.peer_nodes[0]
        self.healthy_nodes = [self.ms_node, self.peer_nodes[1]]
        self.removed_node_url = self.get_node_url_from_filename(
            self.ms_node, self.removed_node)

        self.vcs_cluster_path = self.find(self.ms_node, "/deployments",
                                          "vcs-cluster")[0]
        self.services_path = self.find(self.ms_node, self.vcs_cluster_path,
                                       'collection-of-clustered-service')[0]
        self.service_groups_paths = self.find(self.ms_node, self.services_path,
                                               'vcs-clustered-service')
        self.node_path = self.find(self.ms_node, self.vcs_cluster_path,
                                   'collection-of-node')[0]

        self.node_xml_file = "/tmp/{0}.xml".format(self.removed_node)
        self.services_xml_file = "/tmp/services.xml"

    def tearDown(self):
        """ Runs after every single test """
        super(Story194485, self).tearDown()

    def assert_no_errors_msgs(self, start_pos):
        """
        Description:
            Ensures that no "ERROR" or "WARNING:" messages are
            logged to /var/log/messages on the MS from the
            line specified to the end of the file.
        Args:
            start_pos (int): Line of file to check from.
        """
        msgs_to_check = ["WARNING:", "ERROR"]
        for msg in msgs_to_check:
            msg_found = self.wait_for_log_msg(
                self.ms_node, msg, log_len=start_pos, timeout_sec=1,
                return_log_msgs=True)

            if msg_found:
                # Ignoring postgres errors due to TORF-252951
                errors = [err_msg for err_msg in msg_found
                          if "postgres" not in err_msg]

                self.assertTrue(errors == [], "'{0}' message(s) found in {1}"
                                .format(msg, const.GEN_SYSTEM_LOG_PATH))

    def check_path_not_in_model(self, path_to_check, item_type):
        """
        Description:
            Ensures that the specified path does not exist in the LITP model.
        Args:
            path_to_check (str): Path to check in the LITP model.
            item_type (str): The resource type to filter by.
        """
        self.assertEqual([], self.find(self.ms_node, path_to_check,
                                       item_type, assert_not_empty=False))

    def check_hosts_file(self, node_hostname, nodes_to_check,
                         expected_present=True):
        """
        Description:
            Ensures that a hostname is present or absent
            from the /etc/hosts file of a list of nodes.
        Args:
            node_hostname (str): Hostname of node to check.
            nodes_to_check (list): Nodes to check for in /etc/hosts file.

        Kwargs:
             expected_present (bool): True if the node
             should be referenced, otherwise False.
             Default is True
        """
        cmd = '{0} {1} {2}'.format(const.GREP_PATH, node_hostname,
                                   const.ETC_HOSTS)
        for node in nodes_to_check:
            stdout, _, rc = self.run_command(node, cmd)
            if expected_present:
                self.assertNotEqual([], stdout)
            else:
                self.assertEqual([], stdout)
                self.assertNotEqual(0, rc)

    @attr('all', 'revert', 'story194485', 'story194485_tc02')
    def test_02_p_remove_node_hosts_files(self):
        """
            @tms_id: torf_194485_tc02
            @tms_requirements_id: TORF-194485
            @tms_title: Node Entry Removed From All Other Nodes /etc/hosts File
            @tms_description:
                When I issue the 'litp remove' command to remove a node item
                from the model followed by 'litp create_plan' and
                'litp run_plan' commands, then the plan is successfully
                created, runs to completion and removes the node entry in the
                /etc/hosts file on each remaining node.
            @tms_test_steps:
                @step: Export XML for items that will be removed so they can
                       be re-imported after the test.
                @result: XML exported successfully
                @step: Remove non-modelled dependent package ghostscript-cups
                @result: ghostscript-cups is removed
                @step: Remove each service group from cluster and run plan
                @result: All service groups transition to 'ForRemoval' state
                        and plan runs successfully
                @step: Verify that the service group items have been deleted
                       from model and that the hostname of node to be removed
                       is present in all other host files before test.
                @result: Service group items no longer in model, node hostname
                         present in all host files
                @step: Power off node to be removed. Remove node from model
                       and run plan.
                @result: Node shuts down, it transitions to 'ForRemoval' state
                         and plans runs successfully.
                @step: Verify that the node item has been deleted from the
                        model and that the hostname of removed node is not
                        present in any remaining host files.
                @result: Node item no longer in model. Hostname not found in
                        hosts files
                @step: Verify 'unknown host' error is returned when attempting
                       to ping the host. Assert that no 'Error'/'Warning'
                       messages were logged
                @result: Correct error returned and no errors found in logs.
                @step: Re-add removed node to the model. Run plan ensuring node
                       has been re-added to model and is in state 'Applied'.
                @result: Node re-added, Plan runs successfully. Node in model
                        in 'Applied' state
                @step: Verify hostname of re-added node is
                       present in all other host files
                @result: Hostname verified to be present in all files
                @step: Re-add removed service groups to model, Run plan and
                       ensure all service groups have been re-added to the
                       model and are in state 'Applied'.
                @result: All service groups re-added to
                        model. Plan runs successfully and all service groups
                        are in state 'Applied'.

            @tms_test_precondition: There is more than 1 node in
                the cluster, node to be removed is offline.
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Export XML for items that will be removed so "
                         "they can be re-imported after the test")
        self.execute_cli_export_cmd(self.ms_node, self.services_path,
                                    filepath=self.services_xml_file)

        self.execute_cli_export_cmd(self.ms_node, self.removed_node_url,
                                    filepath=self.node_xml_file)

        try:
            # FOR NODE REMOVAL TO WORK, ALL SERVICE
            # GROUPS MUST BE REMOVED FROM THE CLUSTER
            self.log("info", "# 2. Remove each service group from cluster and "
                             "run plan")
            self.log("info",
                     "# 2a. Remove any non-modelled dependant packages")
            cmd = "{0} -e ghostscript-cups --nodeps".format(const.RPM_PATH)
            self.run_puppet_once(self.ms_node)
            for node in self.peer_nodes:
                rpm_rm_out, _, _ = self.run_command(node, cmd, su_root=True,
                                                   default_asserts=True)
                self.assertEqual([], rpm_rm_out,
                                 "rpm command did not execute as expected")

            service_groups = []
            for service_group in self.service_groups_paths:
                # ADD EACH SERVICE GROUP TO A LIST SO THAT WE CAN CHECK
                # THAT THEY HAVE BEEN ADDED BACK IN AFTER RE-EXPANDING
                service_groups.append(service_group)

                self.log("info", "Removing '{0}'".format(service_group))
                self.execute_cli_remove_cmd(self.ms_node, service_group)

            self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                    plan_timeout_mins=25)

            self.log("info", "# 3. Verify that the service group items "
                             "have been deleted from model and that the "
                             "hostname of node to be removed is present in "
                             "all other host files before test.")
            self.check_path_not_in_model(self.services_path,
                                         'vcs-clustered-service')
            self.check_hosts_file(self.removed_node, self.healthy_nodes)

            start_log_pos = self.get_file_len(
                self.ms_node, const.GEN_SYSTEM_LOG_PATH)

            self.turn_on_litp_debug(self.ms_node)

            self.log('info', '# 4. Power off the node to be removed. Remove '
                             'node from the model. Run plan')
            if self.is_ip_pingable(self.ms_node, self.removed_node):
                self.poweroff_peer_node(self.ms_node, self.removed_node)

            self.execute_cli_remove_cmd(self.ms_node, self.removed_node_url)

            self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                    plan_timeout_mins=25)

            self.log("info", "# 5. Verify that the node item "
                             "has been deleted from the model. "
                             "and that the hostname of removed node is "
                             "not present in any remaining host files.")
            self.check_path_not_in_model(self.removed_node_url, 'node')

            self.check_hosts_file(self.removed_node, self.healthy_nodes,
                                  expected_present=False)

            self.log("info", "# 6. Verify 'unknown host' error is returned "
                             "when attempting to ping the host. Assert "
                             "that no 'ERROR' or 'WARNING' messages were "
                             "logged to {0}.".format(
                                const.GEN_SYSTEM_LOG_PATH))
            # NB: This is a temporary workaround until TORF-474639 is
            # implemented.
            # Workaround, stop puppet, remove search line from
            # resolv.conf, start puppet after ping
            # TORF-544225 is tech debt ticket to remove workaround
            stop_puppet_cmd = self.rhc.get_systemctl_stop_cmd("puppet")
            self.run_command(self.ms_node, stop_puppet_cmd, su_root=True,
                             default_asserts=True)

            sed_cmd = "{0} -i '/search/d' {1}".format(const.SED_PATH,
                                                      const.RESOLV_CFG_FILE)
            self.run_command(self.ms_node, sed_cmd, su_root=True,
                             default_asserts=True)

            cmd = self.net.get_ping_cmd(self.removed_node)
            stdout, _, rc = self.run_command(self.ms_node, cmd, su_root=True)
            self.assertEqual(stdout[0], 'ping: {0}: Name or service not known'
                             .format(self.removed_node))
            self.assertNotEqual(0, rc)

            self.assert_no_errors_msgs(start_log_pos)

            start_puppet_cmd = self.rhc.get_systemctl_start_cmd("puppet")
            self.run_command(self.ms_node, start_puppet_cmd, su_root=True,
                             default_asserts=True)

        finally:
            self.log("info", "# 7. Re-add the removed node to the model. Run "
                             "plan ensuring node has been re-added to model "
                             "and is in state 'Applied'.")
            self.execute_cli_load_cmd(self.ms_node, self.node_path,
                                      self.node_xml_file)

            self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                    plan_timeout_mins=25)

            self.assertEqual('Applied', self.get_item_state(
                self.ms_node, self.removed_node_url))

            self.log("info", "# 8. Set passwords on re-added node.")
            cmd = "{0} -i '/{1}/d' {2}/known_hosts".format(
                const.SED_PATH, self.removed_node, const.SSH_KEYS_FOLDER)
            stdout, _, rc = self.run_command(self.ms_node, cmd)
            self.assertEqual(0, rc)

            self.assertTrue(self.set_pws_new_node(
                self.ms_node, self.removed_node), "Failed to set password.")

            self.log("info", "# 9. Verify hostname of re-added node"
                             "is present in all other host files.")
            self.check_hosts_file(self.removed_node, self.healthy_nodes)

            self.log("info", "# 10. Re-add removed service groups to the "
                             "model then run a plan ensuring all service "
                             "groups have been re-added to the model and are "
                             "in state 'Applied'.")
            self.execute_cli_load_cmd(self.ms_node, self.vcs_cluster_path,
                                      self.services_xml_file, args="--merge")

            self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                    plan_timeout_mins=30)

            for service_group in service_groups:
                self.assertEqual('Applied', self.get_item_state(self.ms_node,
                                                                service_group))
