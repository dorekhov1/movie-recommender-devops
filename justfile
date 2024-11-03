set dotenv-load

default:
    @just --list

clean:
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf __pycache__
    rm -rf .ruff_cache
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    rm -rf .devenv*
    rm -rf .direnv*

install:
    pip install -r requirements.txt

lint:
    ruff check .

format:
    ruff format .

check: lint format

test:
    python -m pytest tests/ 

train:
    python training/train.py

build:
    docker build -t recommender-proper:latest -f ./proper_solution/Dockerfile .
    docker build -t recommender-fallback:latest -f ./fallback_solution/Dockerfile .

run-proper:
    uvicorn proper_solution.app:app --reload --port 5000

run-fallback:
    uvicorn fallback_solution.app:app --reload --port 5000

ci: clean install check test train build

k8s-start:
    minikube start
    minikube addons enable ingress

k8s-use-docker:
    @eval $(minikube docker-env)

k8s-build:
    @eval $(minikube docker-env) && \
    docker build -t recommender-proper:latest -f ./proper_solution/Dockerfile . && \
    docker build -t recommender-fallback:latest -f ./fallback_solution/Dockerfile .

k8s-verify-images:
    @eval $(minikube docker-env) && docker images | grep recommender

k8s-clean-all:
    kubectl delete -f k8s/ || true
    @eval $(minikube docker-env) && \
    docker rmi recommender-proper:latest recommender-fallback:latest || true

k8s-deploy: k8s-clean-all k8s-build
    kubectl apply -f k8s/

k8s-apply:
    kubectl apply -f k8s/deployments.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml

k8s-delete:
    kubectl delete -f k8s/deployments.yaml
    kubectl delete -f k8s/ingress.yaml
    kubectl delete -f k8s/service.yaml

k8s-status:
    kubectl get all
    kubectl get ingress

k8s-logs:
    kubectl logs -l app=recommender --tail=100

k8s-get-url:
    @echo "Service URL: $(minikube ip)"
    @echo "Add to /etc/hosts: $(minikube ip) recommender.local"

k8s-clean: k8s-delete
    minikube stop
    minikube delete

k8s-port-forward:
    kubectl port-forward svc/recommender-service 5000:80 > port-forward.log 2>&1 &
    @echo "Port forwarding started in background. To kill it, run: just k8s-port-forward-stop"

k8s-port-forward-stop:
    pkill -f 'port-forward' || true

k8s-break-proper:
    kubectl scale deployment recommender-proper --replicas=0

k8s-fix-proper:
    kubectl scale deployment recommender-proper --replicas=2

k8s-watch-failover:
    kubectl get pods -w

k8s-describe-pods:
    kubectl describe pods
