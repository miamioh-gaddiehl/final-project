pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'
        DOCKER_IMAGE = 'cithit/gaddiehl'
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-gaddiehl/final-project.git'
        KUBECONFIG = credentials('gaddiehl-225')
    }

    stages {
        stage('Code Checkout') {
            steps {
                cleanWs()
                checkout([$class: 'GitSCM', branches: [[name: '*/main']],
                          userRemoteConfigs: [[url: "${GITHUB_URL}"]]])
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${IMAGE_TAG}", "-f Dockerfile.build .")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${DOCKER_IMAGE}:${IMAGE_TAG}").push()
                    }
                }
            }
        }

        stage('Deploy to Dev Environment') {
            steps {
                script {
                    def kubeConfig = readFile(KUBECONFIG)
                    sh "kubectl delete --all deployments --namespace=default"
                    sh "sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment-dev.yaml"
                    sh "kubectl apply -f deployment-dev.yaml"
                }
            }
        }

        stage("Run Acceptance Tests") {
            steps {
                script {
                    def flaskNode = sh(
                        script: "kubectl get pods -l app=flask-dev -o jsonpath='{.items[0].spec.nodeName}'",
                        returnStdout: true
                    ).trim()

                    def nodeIp = sh(
                        script: "kubectl get node ${flaskNode} -o jsonpath='{.status.addresses[?(@.type==\"InternalIP\")].address}'",
                        returnStdout: true
                    ).trim()

                    sh 'docker stop qa-tests || true'
                    sh 'docker rm qa-tests || true'
                    sh 'docker build -t qa-tests -f Dockerfile.test .'

                    sh """
                        docker run --rm qa-tests /bin/bash -c "
                            pytest ./tests/test_static.py &&
                            pytest ./tests/test_dynamic.py --url "http://${nodeIp}:8080"
                        "
                    """
                }
            }
        }


       stage('Deploy to Prod Environment') {
            steps {
                script {
                    sh "sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment-prod.yaml"
                    sh "kubectl apply -f deployment-prod.yaml"
                }
            }
        }

        stage('Check Kubernetes Cluster') {
            steps {
                script {
                    sh "kubectl get all"
                }
            }
        }
    }

//     post {
//
//         success {
//             slackSend color: "good", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
//         }
//         unstable {
//             slackSend color: "warning", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
//         }
//         failure {
//             slackSend color: "danger", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
//         }
//     }
}
