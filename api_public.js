const http = require('http');
const fs = require('fs');
const path = require('path');

const PUERTO = 8340;
const BURN_ADDRESS = 'drc_quemafuegosolar0000000000000';

const archivos = {
    bloques: path.join(__dirname, 'frontend', 'web', 'bloques.json'),
    saldos: path.join(__dirname, 'frontend', 'web', 'saldos.json'),
    productos: path.join(__dirname, 'frontend', 'web', 'productos.json'),
    quemas: path.join(__dirname, 'frontend', 'web', 'transacciones.json')
};

function leerJSON(ruta) {
    try {
        if (!fs.existsSync(ruta)) return {};
        return JSON.parse(fs.readFileSync(ruta, 'utf8'));
    } catch(e) { return {}; }
}

function responder(res, codigo, datos) {
    res.writeHead(codigo, {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json; charset=utf-8'
    });
    res.end(JSON.stringify(datos, null, 2));
}

const server = http.createServer((req, res) => {
    if (req.method === 'OPTIONS') {
        res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
        res.end();
        return;
    }
    const url = new URL(req.url, `http://localhost:${PUERTO}`);
    const ruta = url.pathname;

    if (ruta === '/api/public' || ruta === '/api/public/docs') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
        res.end(`<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>API DirecCoin</title><style>*{margin:0;padding:0}body{font-family:Inter,sans-serif;background:#050510;color:#f0f0ff;padding:2rem}.container{max-width:800px;margin:0 auto}h1{background:linear-gradient(135deg,#FFE5A0,#FFD700,#FFA500);-webkit-background-clip:text;background-clip:text;color:transparent;font-size:2rem}.sub{color:#7b7f9a;margin-bottom:2rem}.endpoint{background:rgba(14,16,28,.8);border:1px solid rgba(255,215,0,.1);border-radius:16px;padding:1.2rem;margin-bottom:1rem}.method{display:inline-block;background:#00e676;color:#000;padding:3px 10px;border-radius:8px;font-weight:700;font-size:.7rem;margin-right:.8rem}.url{font-family:monospace;color:#FFD700;font-size:.85rem}.desc{color:#7b7f9a;margin-top:.4rem;font-size:.8rem}a{color:#FF6B35;text-decoration:none;font-size:.75rem;display:inline-block;margin-top:.5rem}</style></head><body><div class="container"><h1>🔥 API Pública DirecCoin v1.0</h1><p class="sub">Blockchain L1 · PoUC · IA · Marketplace</p><div class="endpoint"><span class="method">GET</span><span class="url">/api/public/blockchain/info</span><div class="desc">Altura, supply, último bloque</div><a href="/api/public/blockchain/info">Probar →</a></div><div class="endpoint"><span class="method">GET</span><span class="url">/api/public/transacciones?limite=10</span><div class="desc">Últimas transacciones</div><a href="/api/public/transacciones?limite=5">Probar →</a></div><div class="endpoint"><span class="method">GET</span><span class="url">/api/public/marketplace/productos</span><div class="desc">Productos del marketplace</div><a href="/api/public/marketplace/productos">Probar →</a></div><div class="endpoint"><span class="method">GET</span><span class="url">/api/public/burn/stats</span><div class="desc">DRC quemados totales</div><a href="/api/public/burn/stats">Probar →</a></div><div class="endpoint"><span class="method">GET</span><span class="url">/api/public/wallet/:direccion</span><div class="desc">Saldo público</div><a href="/api/public/wallet/drc_enviopactocunaaurorabaseritm">Probar →</a></div></div></body></html>`);
        return;
    }

    if (ruta === '/api/public/blockchain/info') {
        const data = leerJSON(archivos.bloques) || {};
        const bloques = data.bloques || [];
        const saldos = leerJSON(archivos.saldos) || {};
        let supply = 0;
        for (const addr in saldos) supply += saldos[addr] || 0;
        responder(res, 200, {
            altura: data.ultimo_bloque || bloques.length,
            bloquesMinados: bloques.length,
            supplyTotal: supply,
            ultimoBloque: bloques[bloques.length - 1] || null
        });
        return;
    }

    if (ruta === '/api/public/transacciones') {
        const limite = parseInt(url.searchParams.get('limite')) || 20;
        const txs = leerJSON(archivos.quemas) || [];
        const lista = Array.isArray(txs) ? txs : (txs.confirmadas || []);
        responder(res, 200, { total: lista.length, transacciones: lista.slice(-limite).reverse() });
        return;
    }

    if (ruta === '/api/public/marketplace/productos') {
        const productos = leerJSON(archivos.productos) || [];
        const publicos = (Array.isArray(productos) ? productos : []).filter(p => !p.oculto).map(p => ({
            id: p.id, titulo: p.titulo || p.nombre, precio: p.precio,
            vendedor: p.vendedor, fecha: p.fecha
        }));
        responder(res, 200, { total: publicos.length, productos: publicos });
        return;
    }

    if (ruta === '/api/public/burn/stats') {
        const txs = leerJSON(archivos.quemas) || [];
        const lista = Array.isArray(txs) ? txs : (txs.confirmadas || []);
        let totalQuemado = 0, txQuema = 0;
        for (const tx of lista) {
            if (tx.destino === BURN_ADDRESS || tx.tipo === 'quema') { totalQuemado += tx.cantidad || 0; txQuema++; }
        }
        responder(res, 200, { direccionQuema: BURN_ADDRESS, totalQuemado, transaccionesQuema: txQuema });
        return;
    }

    if (ruta.startsWith('/api/public/wallet/')) {
        const dir = ruta.split('/')[4];
        const saldos = leerJSON(archivos.saldos) || {};
        responder(res, 200, { direccion: dir, saldo: saldos[dir] || 0 });
        return;
    }

    responder(res, 404, { error: 'Endpoint no encontrado' });
});

server.listen(PUERTO, '0.0.0.0', () => console.log('🔥 API Pública puerto', PUERTO));
