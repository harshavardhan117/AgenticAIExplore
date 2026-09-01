# Deployment notes

`oracle-23ai-vector.yaml` is an optional single-node Kubernetes learning deployment for Oracle Database 23ai and vector search. It creates a persistent Oracle database and initializes a vector user from a Kubernetes Secret.

## Before applying

1. Use a dedicated namespace and revise all resource names for your environment.
2. Create a Kubernetes Secret outside Git with strong database passwords.
3. Confirm the cluster has sufficient CPU, memory, and persistent storage.
4. Keep the database private by default; expose it only through an approved network path.

The manifest reads passwords only through `secretKeyRef`; it contains no real password values. Do not place a Secret manifest with literal credentials in this repository.

## Scope

This deployment is provided for local learning and prototyping. Production deployments need backup strategy, network policies, TLS, resource monitoring, database patching, high availability, and organization-approved secret management.
