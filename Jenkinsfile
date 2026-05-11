pipeline {
    agent any // This allows us to use specific agents for each stage

    environment {
        BACKEND_IMAGE = "autolead-backend"
        FRONTEND_IMAGE = "autolead-frontend"
        GAR_REGION = "asia-south1"
        GAR_REPOSITORY = "autolead"
        CLOUD_RUN_REGION = "asia-south1"
        BACKEND_SERVICE_NAME = "autolead-backend"
        WORKER_SERVICE_NAME = "autolead-worker"
        FRONTEND_SERVICE_NAME = "autolead-frontend"
        DEPLOY_BRANCH = "main"

        // Deployment Configuration
        GCP_PROJECT_ID = "gen-lang-client-0898802422"
        GCP_SA_CREDENTIALS_ID = "GCP_SA_CREDENTIALS_ID"
        BACKEND_ENV_VARS_FILE_CREDENTIALS_ID = "BACKEND_ENV_VARS_FILE_CREDENTIALS_ID"
        
        // Update this with your actual backend Cloud Run URL after the first deployment
        FRONTEND_API_URL = "https://autolead-backend-gen-lang-client.a.run.app/api/v1"
    }

    stages {
        stage('Backend Tests') {
            agent {
                docker { 
                    image 'python:3.11-slim' 
                    reuseNode true
                }
            }
            steps {
                dir('backend') {
                    echo 'Installing backend dependencies and testing...'
                    sh 'pip install --no-cache-dir -r requirements-dev.txt'
                    // sh 'pytest' // Uncomment when you have tests
                }
            }
        }

        stage('Frontend Build & Lint') {
            agent {
                docker { 
                    image 'node:20-alpine' 
                    reuseNode true
                }
            }
            steps {
                dir('frontend') {
                    echo 'Installing frontend dependencies...'
                    sh 'npm install'
                    sh 'npm run lint'
                    echo 'Running a test build...'
                    sh 'npm run build'
                }
            }
        }

        stage('Build Production Images') {
            // This stage runs on the main agent because it needs access to the host's Docker socket
            steps {
                echo 'Building final production-ready Docker images...'
                script {
                    sh "docker build -t ${BACKEND_IMAGE}:latest ./backend"
                    sh """
                        docker build \
                          --build-arg NEXT_PUBLIC_API_URL=${env.FRONTEND_API_URL ?: 'http://127.0.0.1:8000/api/v1'} \
                          -f ./frontend/Dockerfile.prod \
                          -t ${FRONTEND_IMAGE}:latest \
                          ./frontend
                    """
                }
            }
        }

        stage('Push Images to Artifact Registry') {
            agent {
                docker { 
                    image 'google/cloud-sdk:latest' 
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                    reuseNode true
                }
            }
            when {
                expression {
                    return env.GCP_PROJECT_ID?.trim() && env.GCP_SA_CREDENTIALS_ID?.trim()
                }
            }
            steps {
                script {
                    def registry = "${env.GAR_REGION}-docker.pkg.dev/${env.GCP_PROJECT_ID}/${env.GAR_REPOSITORY}"
                    withCredentials([file(
                        credentialsId: env.GCP_SA_CREDENTIALS_ID,
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )]) {
                        sh '''
                            gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                            gcloud auth configure-docker ${GAR_REGION}-docker.pkg.dev --quiet
                            docker tag ${BACKEND_IMAGE}:latest ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:${BUILD_NUMBER}
                            docker tag ${BACKEND_IMAGE}:latest ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:latest
                            docker tag ${FRONTEND_IMAGE}:latest ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${FRONTEND_IMAGE}:${BUILD_NUMBER}
                            docker tag ${FRONTEND_IMAGE}:latest ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${FRONTEND_IMAGE}:latest
                            docker push ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:${BUILD_NUMBER}
                            docker push ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:latest
                            docker push ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${FRONTEND_IMAGE}:${BUILD_NUMBER}
                            docker push ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${FRONTEND_IMAGE}:latest
                        '''
                    }
                }
            }
        }

        stage('Deploy Backend to Cloud Run') {
            agent {
                docker { 
                    image 'google/cloud-sdk:latest' 
                    reuseNode true
                }
            }
            when {
                expression {
                    def hasDeployConfig = env.GCP_PROJECT_ID?.trim() &&
                        env.GCP_SA_CREDENTIALS_ID?.trim() &&
                        env.BACKEND_ENV_VARS_FILE_CREDENTIALS_ID?.trim()
                    def branchMatches = !env.BRANCH_NAME?.trim() || env.BRANCH_NAME == env.DEPLOY_BRANCH
                    return hasDeployConfig && branchMatches
                }
            }
            steps {
                script {
                    def registry = "${env.GAR_REGION}-docker.pkg.dev/${env.GCP_PROJECT_ID}/${env.GAR_REPOSITORY}"
                    withCredentials([
                        file(credentialsId: env.GCP_SA_CREDENTIALS_ID, variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                        file(credentialsId: env.BACKEND_ENV_VARS_FILE_CREDENTIALS_ID, variable: 'BACKEND_ENV_FILE')
                    ]) {
                        sh '''
                            gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                            gcloud config set project ${GCP_PROJECT_ID}
                            gcloud run deploy ${BACKEND_SERVICE_NAME} \
                              --image ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:${BUILD_NUMBER} \
                              --region ${CLOUD_RUN_REGION} \
                              --platform managed \
                              --allow-unauthenticated \
                              --port 8000 \
                              --env-vars-file "$BACKEND_ENV_FILE"
                        '''
                    }
                }
            }
        }

        stage('Deploy Worker to Cloud Run') {
            agent {
                docker { 
                    image 'google/cloud-sdk:latest' 
                    reuseNode true
                }
            }
            when {
                expression {
                    def hasDeployConfig = env.GCP_PROJECT_ID?.trim() &&
                        env.GCP_SA_CREDENTIALS_ID?.trim() &&
                        env.BACKEND_ENV_VARS_FILE_CREDENTIALS_ID?.trim()
                    def branchMatches = !env.BRANCH_NAME?.trim() || env.BRANCH_NAME == env.DEPLOY_BRANCH
                    return hasDeployConfig && branchMatches
                }
            }
            steps {
                script {
                    def registry = "${env.GAR_REGION}-docker.pkg.dev/${env.GCP_PROJECT_ID}/${env.GAR_REPOSITORY}"
                    withCredentials([
                        file(credentialsId: env.GCP_SA_CREDENTIALS_ID, variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                        file(credentialsId: env.BACKEND_ENV_VARS_FILE_CREDENTIALS_ID, variable: 'BACKEND_ENV_FILE')
                    ]) {
                        // Note: We use --no-cpu-throttling for Always-on CPU to ensure the worker keeps processing tasks
                        sh '''
                            gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                            gcloud config set project ${GCP_PROJECT_ID}
                            gcloud run deploy ${WORKER_SERVICE_NAME} \
                              --image ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${BACKEND_IMAGE}:${BUILD_NUMBER} \
                              --region ${CLOUD_RUN_REGION} \
                              --platform managed \
                              --no-allow-unauthenticated \
                              --command "celery" \
                              --args="-A,app.celery_app.celery_app,worker,--loglevel=info" \
                              --no-cpu-throttling \
                              --min-instances 1 \
                              --env-vars-file "$BACKEND_ENV_FILE"
                        '''
                    }
                }
            }
        }

        stage('Deploy Frontend to Cloud Run') {
            agent {
                docker { 
                    image 'google/cloud-sdk:latest' 
                    reuseNode true
                }
            }
            when {
                expression {
                    def hasDeployConfig = env.GCP_PROJECT_ID?.trim() &&
                        env.GCP_SA_CREDENTIALS_ID?.trim()
                    def branchMatches = !env.BRANCH_NAME?.trim() || env.BRANCH_NAME == env.DEPLOY_BRANCH
                    return hasDeployConfig && branchMatches
                }
            }
            steps {
                script {
                    def registry = "${env.GAR_REGION}-docker.pkg.dev/${env.GCP_PROJECT_ID}/${env.GAR_REPOSITORY}"
                    withCredentials([file(
                        credentialsId: env.GCP_SA_CREDENTIALS_ID,
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )]) {
                        sh '''
                            gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                            gcloud config set project ${GCP_PROJECT_ID}
                            gcloud run deploy ${FRONTEND_SERVICE_NAME} \
                              --image ${GAR_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPOSITORY}/${FRONTEND_IMAGE}:${BUILD_NUMBER} \
                              --region ${CLOUD_RUN_REGION} \
                              --platform managed \
                              --allow-unauthenticated \
                              --port 3000
                        '''
                    }
                }
            }
        }

        stage('Cleanup') {
            steps {
                echo 'Cleaning up dangling images...'
                sh 'docker image prune -f'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Autolead is ready for deployment!'
        }
        failure {
            echo 'FAILURE: The build failed. Check the logs above.'
        }
    }
}
