NAMESPACE=trivy-ui
K8S_DIR=trivy-ui/k8s/postgres
DOCKER_REPO=camelel
#DOCKER_REPO=host.docker.internal:5001


build-backend:
	docker build --no-cache -t $(DOCKER_REPO)/trivy-ui-backend:latest -f backend/Dockerfile backend

build-frontend:
	docker build -t $(DOCKER_REPO)/trivy-ui-frontend:latest -f frontend/Dockerfile frontend

build-all:
	docker build -t $(DOCKER_REPO)/trivy-ui-backend:latest -f backend/Dockerfile backend
	docker build -t $(DOCKER_REPO)/trivy-ui-frontend:latest -f frontend/Dockerfile frontend

push-all:
	docker push $(DOCKER_REPO)/trivy-ui-backend:latest
	docker push $(DOCKER_REPO)/trivy-ui-frontend:latest

push-backend:
#	docker tag trivy-ui-backend:latest $(DOCKER_REPO)/trivy-ui-backend:latest
	docker push $(DOCKER_REPO)/trivy-ui-backend:latest
# Push targets
push-backend:
	docker push $(DOCKER_REPO)/trivy-ui-backend:latest

push-frontend:
	docker push $(DOCKER_REPO)/trivy-ui-frontend:latest

push-all:
	docker push $(DOCKER_REPO)/trivy-ui-backend:latest
	docker push $(DOCKER_REPO)/trivy-ui-frontend:latest
#	kubectl apply -f $(K8S_DIR)/psql_secret.yaml -n $(NAMESPACE)
	kubectl apply -f $(K8S_DIR)/psql_configmap.yaml -n $(NAMESPACE)
	kubectl apply -f $(K8S_DIR)/psql_deployment.yaml -n $(NAMESPACE)
	kubectl apply -f $(K8S_DIR)/postgres_service.yaml -n $(NAMESPACE)

wait-db:
	kubectl wait --for=condition=ready pod -l app=postgres -n $(NAMESPACE) --timeout=90s

init-db:
	kubectl exec -it deployment/trivy-ui-backend -n $(NAMESPACE) -- \
		python3 -m scripts.postgres_init_schema

deploy-app:
	kubectl apply -f k8s/backend/backend-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f k8s/frontend/frontend-deployment.yaml -n $(NAMESPACE)
	kubectl apply -f k8s/ingress/ingress-deployment.yaml -n $(NAMESPACE)

replace-app:
	kubectl replace -f k8s/backend/backend-deployment.yaml -n $(NAMESPACE)
	kubectl replace -f k8s/frontend/frontend-deployment.yaml -n $(NAMESPACE)

rollout-backend:
	kubectl rollout restart deployment/trivy-ui-backend -n $(NAMESPACE)

rollout-frontend:
	kubectl rollout restart deployment/trivy-ui-frontend -n $(NAMESPACE)

rollout-all:
	kubectl rollout restart deployment/trivy-ui-backend -n $(NAMESPACE)
	kubectl rollout restart deployment/trivy-ui-frontend -n $(NAMESPACE)

setup:
	make deploy-db
	make wait-db
	make deploy-app
	make init-db

build-push-backend:
	make build-backend
	make push-backend

build-push-frontend:
	make build-frontend
	make push-frontend

build-push-all:
	make build-all
	make push-all

build-push-rollout:
	make build-all
	make push-all
	make rollout-backend
	make rollout-frontend
