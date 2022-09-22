# This script generates Pods in Pending state

for ns in `kubectl get namespaces --no-headers | awk '{print $1}'`; do
    pod_name="test-pod-$(( $RANDOM % 5000 + 1 ))"
    echo Creating pod $pod_name in namespace $ns
    kubectl --namespace $ns run $pod_name --image=wrongimage
    # kubectl --namespace $ns delete pod $pod_name
done

# echo Non Running State Pods
# kubectl get pods --field-selector status.phase!=Running --all-namespaces

echo
kubectl get pods --field-selector status.phase=Pending --all-namespaces
echo Pods in Pending State: $(kubectl get pods --field-selector status.phase=Pending --all-namespaces --no-headers | wc -l)
