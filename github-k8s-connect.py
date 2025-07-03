from os import listdir, makedirs
import subprocess
import json
import requests

# Function to load configuration from config.json
def load_config():
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            required_keys = ["GITHUB_ACCESS_TOKEN", "GITHUB_REPOSITORY", "ABSPATH_TO_PROJECT"]
            for key in required_keys:
                if key not in config or not config[key]:
                    raise ValueError(f"Missing or empty value for {key} in config.json")
            return config
    except FileNotFoundError:
        print("Error: config.json file not found in the current directory.")
        exit(1)
    except json.JSONDecodeError:
        print("Error: config.json is not a valid JSON file.")
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

# Load configuration
config = load_config()

# Extract values from config
GITHUB_ACCESS_TOKEN = config["GITHUB_ACCESS_TOKEN"]  # GitHub Personal Access Token
GITHUB_REPO = config["GITHUB_REPOSITORY"]           # GitHub repository in format 'owner/repo'
ABSPATH_TO_PROJECT = config["ABSPATH_TO_PROJECT"]   # Absolute path to the project directory
GITHUB_WORKFLOW_NAME = "Kubernetes-Deploy"          # Default workflow name since not in config.json

# Function to check if a GitHub repository exists
def check_repo():
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {
        'Authorization': f'token {GITHUB_ACCESS_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Repository {GITHUB_REPO} not found or inaccessible.")
        print(response.text)
        exit(1)
    return response.json()

# Function to create or update a GitHub Actions workflow for k8s deployment
def setup_workflow():
    workflow_path = f"{ABSPATH_TO_PROJECT}/.github/workflows/deploy.yml"
    makedirs(f"{ABSPATH_TO_PROJECT}/.github/workflows", exist_ok=True)

    # Basic GitHub Actions workflow for Kubernetes deployment
    workflow_content = f"""
name: {GITHUB_WORKFLOW_NAME}
on:
  push:
    branches:
      - main
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      - name: Configure Kubernetes context
        run: |
          echo "${{ secrets.KUBE_CONFIG }}" > kubeconfig
          export KUBECONFIG=kubeconfig
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
    """
    with open(workflow_path, "w") as f:
        f.write(workflow_content)
    print(f"GitHub Actions workflow created at {workflow_path}")

# Function to initialize Helm and deploy a sample Helm chart (if needed)
def install_helm_chart():
    try:
        print("Setting up Helm repositories...")
        subprocess.check_call('helm repo add bitnami https://charts.bitnami.com/bitnami', shell=True)
        subprocess.check_call('helm repo update', shell=True)
        print("Installing a sample Helm chart (e.g., nginx)...")
        subprocess.check_call(
            'helm upgrade --install sample-nginx bitnami/nginx --namespace default', shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during Helm setup: {e}")
        exit(1)

# Function to ensure Kubernetes manifests are in the project
def setup_k8s_manifests():
    k8s_dir = f"{ABSPATH_TO_PROJECT}/k8s"
    makedirs(k8s_dir, exist_ok=True)
    
    # Example: Create a simple Nginx deployment manifest if none exists
    manifest_path = f"{k8s_dir}/nginx-deployment.yaml"
    if not any(f.endswith('.yaml') for f in listdir(k8s_dir)):
        manifest_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
        """
        with open(manifest_path, "w") as f:
            f.write(manifest_content)
        print(f"Sample Kubernetes manifest created at {manifest_path}")
    else:
        print(f"Kubernetes manifests already exist in {k8s_dir}")

# Main execution
if __name__ == "__main__":
    print(f"Checking GitHub repository {GITHUB_REPO}...")
    check_repo()

    print("Setting up Kubernetes manifests...")
    setup_k8s_manifests()

    print("Setting up GitHub Actions workflow for deployment...")
    setup_workflow()

    print("Setting up Helm for Kubernetes deployments (optional)...")
    install_helm_chart()

    print("Setup complete. Push your changes to GitHub to trigger deployment.")