# 📦 Task Manager — Monolith App
## Deploy en AWS Linux (via Bastion → EC2)

---

### 1. Conectarse al servidor
```bash
# Desde tu máquina local vía Bastion
ssh -i tu-key.pem -J ec2-user@<BASTION-IP> ec2-user@<APP-SERVER-IP>
```

---

### 2. Instalar dependencias en el servidor
```bash
sudo yum update -y                    # Amazon Linux
sudo yum install python3 python3-pip -y
```

---

### 3. Copiar los archivos al servidor
```bash
# Desde tu máquina local (o usa scp con Bastion como jump)
scp -i tu-key.pem -o "ProxyJump ec2-user@<BASTION-IP>" \
    app.py requirements.txt stress_test.py \
    ec2-user@<APP-SERVER-IP>:~/taskapp/
```

---

### 4. Instalar librerías Python
```bash
cd ~/taskapp
pip3 install -r requirements.txt
```

---

### 5. Configurar variables de entorno (apunta a tu RDS)
```bash
export DB_HOST="tu-rds-endpoint.rds.amazonaws.com"
export DB_PORT="3306"
export DB_USER="admin"
export DB_PASSWORD="tu-password"
export DB_NAME="taskdb"
```
> Tip: agrégalas a ~/.bashrc para que persistan.

---

### 6. Crear la base de datos en RDS
Conéctate desde el servidor (el SG de RDS debe permitir el SG del App Server):
```bash
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "CREATE DATABASE IF NOT EXISTS taskdb;"
```

---

### 7. Correr la aplicación
```bash
python3 app.py
# Escucha en 0.0.0.0:5000
```
Para dejarla corriendo en background:
```bash
nohup python3 app.py > app.log 2>&1 &
```

---

### 8. Abrir el puerto 5000 en el Security Group
En la consola de AWS → EC2 → Security Groups → Inbound Rules:
```
Type: Custom TCP  |  Port: 5000  |  Source: 0.0.0.0/0
```

---

### 9. Acceder a la app
```
http://<APP-SERVER-IP>:5000
```

---

## 🔥 Stress Test

### Opción A — Script Python incluido
```bash
# 500 requests, 50 hilos concurrentes
python3 stress_test.py http://<APP-SERVER-IP>:5000 500 50
```

### Opción B — Apache Bench (ab)
```bash
sudo yum install httpd-tools -y
ab -n 500 -c 50 http://<APP-SERVER-IP>:5000/api/stress
```

### Opción C — curl loop rápido
```bash
for i in {1..100}; do curl -s http://<APP-SERVER-IP>:5000/api/stress & done; wait
```

---

## 📐 Arquitectura Monolito
```
[Browser / Stress Tool]
         |
    [Flask App - port 5000]
     ├── Interface  → HTML embebido en app.py
     ├── Logic      → Rutas Flask + validaciones
     └── Data       → mysql-connector → RDS MySQL
```

Todo en un solo proceso Python — interfaz, lógica y datos. ✅
