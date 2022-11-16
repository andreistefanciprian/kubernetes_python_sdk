"""
This script runs in a k8s cluster and listens for recent Pod Events
with a particular error message across all namespaces.
An error message example could be: Failed to pull image ...

The script goes through this sequence of steps:
- read all recent events across all namespaces
- return a list of Pods that have the error message
- iterate through above Pods list and
    - check if Pod exists
    - wait for a few seconds and check if Pod is still in a Pending state
    - delete Pod if in Pending state

Script executes the above steps every n seconds.
"""

from kubernetes import client, config
import logging
import time
from datetime import datetime, timezone
import os
import signal
import argparse


class K8sClass:

    """
    Deletes Pods in Pending state across all namespaces
    that have error message in Events.
    """

    logging.basicConfig(
        format='%(levelname)s:%(asctime)s:%(message)s',
        level=logging.INFO
        )

    def __init__(self, error_message):
        self.__core_api = client.CoreV1Api()
        self.__namespaces = []
        self.__k8s_client_connected = False
        self.error_message = error_message
        # self.poll_interval = 60 if poll_interval is None else poll_interval
        # self.event_age = event_age

    def __time_track(func):
        """
        Decorator used for measuring time execution of methods.
        """
        def wrapper(*arg, **kw):
            t1 = time.time()
            result = func(*arg, **kw)
            total_time = time.time() - t1
            logging.info(f'{func.__name__} ran in {total_time} seconds.')
            return result
        return wrapper

    # @__time_track 
    def __initialise_client(self):
        if not self.__k8s_client_connected:
            try:
                client.CoreV1Api
            except Exception as e:
                logging.info(e)
                raise
            else:
                logging.info('Connection to K8s client was established.')
                self.__k8s_client_connected = True
                return True
        else:
            return True

    # @__time_track 
    def __get_namespaces(self):
        """"Returns a list of namespaces in the cluster."""
        if self.__initialise_client():
            try:
                result = self.__core_api.list_namespace()
            except Exception as e:
                logging.info(e)
                raise
            else:
                for i in result.items:
                    self.__namespaces.append(i.metadata.name)
            logging.debug(f'Namespaces: {self.__namespaces}')
            return self.__namespaces
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def __verify_pod_exists(self, pod_name, pod_namespace):
        """
        Verifies if Pod exists.
        returns: bool
        """
        if self.__initialise_client():
            logging.debug(f'Verifies if Pod {pod_namespace}/{pod_name} exists.')
            try:
                self.__core_api.read_namespaced_pod(pod_name, pod_namespace)
            except Exception as e:
                logging.debug(e)
                return False
            else:
                return True
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def __delete_pod(self, pod_name, pod_namespace):
        """Deletes Pod."""
        if self.__initialise_client():
            try:
                self.__core_api.delete_namespaced_pod(pod_name, pod_namespace)
            except Exception as e:
                logging.info(f'Pod {pod_name} in namespace {pod_namespace} could not be deleted: \n{e}')
                # raise
            else:
                logging.info(f'Deleted Pod {pod_name} in namespace {pod_namespace}')
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def __get_pod_status(self, pod_name, pod_namespace):
        """"Returns Pod status."""
        if self.__initialise_client():
            logging.debug(f'Getting {pod_namespace}/{pod_name} Pod status')
            try:
                result = self.__core_api.read_namespaced_pod_status(pod_name, pod_namespace)
            except Exception as e:
                logging.info(e)
                # raise
                return ""
            else:
                pod_status = result.status.phase
                logging.debug(f' Pod {pod_namespace}/{pod_name} status is: {pod_status}')
                return pod_status
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def __get_pods_with_error_event(self):
        """
        Returns a list of existing Pods with error message in events.
        return: {(pod_name, pod_namespace),...}
        """
        if self.__initialise_client():
            self.__namespaces = self.__get_namespaces()
            errored_pods = []
            # current_time = datetime.now(timezone.utc)
            for namespace in self.__namespaces:
                try:
                    result = self.__core_api.list_namespaced_event(namespace)
                except Exception as e:
                    logging.info(e)
                    raise
                else:
                    for i in result.items:
                        if i.involved_object.kind == 'Pod':
                            # calculate Event age in seconds
                            # event_age = current_time - i.last_timestamp
                            # if event is recent and contains Error message
                            # if self.error_message in i.message and event_age.seconds < self.event_age:
                            if self.error_message in i.message:
                                event_type = i.type
                                event_reason = i.reason
                                event_message = i.message
                                event_pod = i.involved_object.name
                                event_ns = i.involved_object.namespace
                                logging.debug(f'{event_type} {event_reason} {event_pod} {event_ns} \n{event_message}')
                                if self.__verify_pod_exists(event_pod, event_ns):
                                    if self.__get_pod_status(event_pod, event_ns) == 'Pending':
                                        errored_pods.append((event_pod, event_ns))
                                else:
                                    logging.debug(f"Pod {event_pod} in namespace {event_ns} doesn't exist anymore!")
            errored_pods = list(dict.fromkeys(errored_pods))
            if len(errored_pods) > 0:
                logging.info(f'There are {len(errored_pods)} Pods with Error Event {self.error_message} in Pending state: \n{errored_pods}')
            else:
                logging.info(f'There are {len(errored_pods)} Pods with Error Event {self.error_message} in Pending state.')
            return errored_pods
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def delete_pending_pods(self):
        """Delete Pending Pods with error message from all namespaces."""
        if self.__initialise_client():
            pods_in_pending_state = self.__get_pods_with_error_event()
            if len(pods_in_pending_state) >= 1:
                time.sleep(5)   # wait a few seconds just in case Pod transitions state from Pending to Running
                for pod_name, pod_namespace in pods_in_pending_state:
                    # verify Pod exists
                    if self.__verify_pod_exists(pod_name, pod_namespace):
                        # delete Pod if in Pending state
                        if self.__get_pod_status(pod_name, pod_namespace) == 'Pending':
                            self.__delete_pod(pod_name, pod_namespace)
                    else:
                        logging.info(f"Pod {pod_name} in namespace {pod_namespace} doesn't exist anymore!")
        else:
            logging.info('Connection to K8s client failed.')

    # @__time_track 
    def delete_pending_pods_loop(self):
        """
        Checks events every self.poll_interval seconds for Pending Pods.
        Delete pending pods that have error_message.
        """

        while True:
            self.delete_pending_pods()
            time.sleep(self.poll_interval)


def handler(signum, frame):
    """Catch keyboard interrupt signal and exit gracefully"""
    print("Program was interrupted with CTRL+C")
    exit(0)


def main():

    # define cli params
    parser = argparse.ArgumentParser()
    parser.add_argument('--error-message',
                        type=str,
                        help="Error mesage to search for in Pending Pods.",
                        required=True)
    parser.add_argument('--polling-interval',
                        type=int,
                        default=10,
                        help="Search and delete Pods in Pending state with Error Message every n seconds.",
                        required=False)
    args = parser.parse_args()

    # authenticate k8s client
    kube_auth = os.getenv("KUBE_AUTH_INSIDE_CLUSTER", False)
    if kube_auth:
        config.load_incluster_config()  # inside cluster authentication
    else:
        config.load_kube_config()  # outside cluster authentication

    # delete pending pods loop
    job = K8sClass(
        error_message=args.error_message
        )
    while True:
        print()
        job.delete_pending_pods()
        time.sleep(args.polling_interval)


if __name__ == '__main__':
    # catch keyboard interrupt signal and exit gracefully
    signal.signal(signal.SIGINT, handler)

    # start pod restarter
    main()
