# 🏥 HealthGuard Pro - Sistema de Monitoreo Médico (Microservicios)

HealthGuard Pro es una plataforma de gestión clínica y monitoreo de pacientes. 
Este proyecto representa la evolución de un sistema monolítico a una **arquitectura de microservicios**, separando el frontend (React) del backend (Flask) y dividiendo las responsabilidades del servidor en servicios independientes comunicados a través de un API Gateway.

## 🏗️ Arquitectura del Sistema

El sistema está compuesto por 4 módulos principales y una base de datos compartida:

1. **Frontend (React + Vite)**: Interfaz de usuario (Puerto 5173).
2. **API Gateway (Flask + httpx)**: Punto de entrada único que enruta el tráfico (Puerto 5000).
3. **Auth Service (Flask)**: Gestión de identidad, roles, permisos y emisión de tokens JWT (Puerto 5001).
4. **Clinical Service (Flask)**: Gestión de pacientes, signos vitales, historial y alertas (Puerto 5002).
5. **Base de Datos (MySQL 8)**: Almacenamiento persistente compartido.

### Diagrama de Comunicación
```mermaid
flowchart LR
    A[React\n:5173] -->|HTTP| B(API Gateway\n:5000)
    B -->|/api/auth| C(Auth Service\n:5001)
    B -->|/api/*| D(Clinical Service\n:5002)
    C -->|SQL| E[(MySQL\n:3306)]
    D -->|SQL| E
