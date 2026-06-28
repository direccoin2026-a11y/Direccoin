#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    DIRECCOIN - DEPLOY SCRIPT v2.0                            ║
# ║                    Sube el nodo a Oracle Cloud Free Tier                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

echo "🚀 DIRECCOIN - DESPLIEGUE EN ORACLE CLOUD"
echo "========================================="

# ⚠️ CAMBIA ESTO por tu IP real de Oracle Cloud
NODO_IP="TU_IP_AQUI"
NODO_USUARIO="ubuntu"
NODO_DIR="/home/ubuntu/direccoin"

echo ""
echo "📡 Conectando a $NODO_USUARIO@$NODO_IP..."

# 1. Preparar el servidor
ssh $NODO_USUARIO@$NODO_IP << 'EOF'
    echo ""
    echo "📦 Actualizando sistema..."
    sudo apt update && sudo apt upgrade -y
    
    echo ""
    echo "🐍 Instalando Python y dependencias..."
    sudo apt install python3 python3-pip git ufw -y
    
    echo ""
    echo "📦 Instalando librerías..."
    pip3 install pycryptodome msgpack
    
    echo ""
    echo "🔓 Configurando firewall..."
    sudo ufw allow 8338/tcp comment 'Nodo Direccoin'
    sudo ufw allow 8339/tcp comment 'API Direccoin'
    sudo ufw allow 8080/tcp comment 'Explorador Web'
    sudo ufw --force enable
    
    echo ""
    echo "📁 Creando directorio del proyecto..."
    mkdir -p ~/direccoin/data/blockchain
    mkdir -p ~/direccoin/logs
    
    echo ""
    echo "✅ Servidor preparado"
EOF

# 2. Subir archivos
echo ""
echo "📤 Subiendo archivos de Direccoin..."
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'frontend' \
    --exclude 'billetera/direct.json' \
    --exclude 'billetera/direct_backup.txt' \
    --exclude '*.keystore' \
    ../ $NODO_USUARIO@$NODO_IP:~/direccoin/

# 3. Iniciar servicios
echo ""
echo "⛓️  Iniciando nodo Direccoin..."
ssh $NODO_USUARIO@$NODO_IP << 'EOF'
    cd ~/direccoin
    
    echo "📋 Iniciando nodo minero..."
    nohup python3 red_p2p/nodo.py --modo minero --puerto 8338 > logs/nodo.log 2>&1 &
    echo "   PID: $!"
    
    sleep 2
    
    echo "🌐 Iniciando API REST..."
    nohup python3 api/rest_api.py > logs/api.log 2>&1 &
    echo "   PID: $!"
    
    sleep 2
    
    echo "🔍 Iniciando explorador web..."
    cd frontend/web
    nohup python3 -m http.server 8080 > ../../logs/explorer.log 2>&1 &
    cd ../..
    echo "   PID: $!"
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🎯 DIRECCOIN DESPLEGADO"
    echo "═══════════════════════════════════════════════════════"
    echo "  📡 Nodo P2P:  $NODO_IP:8338"
    echo "  🌐 API REST:  http://$NODO_IP:8339/api/v1/estado"
    echo "  🔍 Explorer:  http://$NODO_IP:8080"
    echo "  📋 Logs:      ~/direccoin/logs/"
    echo "═══════════════════════════════════════════════════════"
EOF

echo ""
echo "🎯 ¡DIRECCOIN ESTÁ VIVO!"
echo ""
echo "📋 Para conectar tu app desktop:"
echo "   Cambia NODO_IP = '$NODO_IP' en main_window.py"
echo ""
echo "📋 Para ver el estado:"
echo "   http://$NODO_IP:8339/api/v1/estado"