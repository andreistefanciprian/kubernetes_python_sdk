from kubernetes import client, config


def main():
    
    config.load_incluster_config()  # inside cluster authentication
    # config.load_kube_config()   # outside cluster authentication

    v1 = client.CoreV1Api()

    # list all pods in all namespaces
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.status.phase == 'Pending':
            try:
                v1.delete_namespaced_pod(i.metadata.name, i.metadata.namespace)
            except Exception as e:
                print(e)
            else:
                print(f'{i.status.phase} pod {i.metadata.name} in namespace {i.metadata.namespace} was deleted!')


if __name__ == '__main__':
    main()