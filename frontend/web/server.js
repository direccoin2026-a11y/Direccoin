const http = require('http');
const fs = require('fs');
const path = require('path');

const PUERTO = 3003;
const ARCHIVO = path.join(__dirname, 'productos.json');
const TXS_FILE = path.join(__dirname, 'transacciones.json');
const ANUNCIOS = path.join(__dirname, 'anuncios.json');
const P2P_FILE = path.join(__dirname, 'p2p.json');
if (!fs.existsSync(P2P_FILE)) fs.writeFileSync(P2P_FILE, '[]', 'utf8');

if (!fs.existsSync(ARCHIVO)) fs.writeFileSync(ARCHIVO, '[]', 'utf8');
if (!fs.existsSync(TXS_FILE)) fs.writeFileSync(TXS_FILE, '[]', 'utf8');
if (!fs.existsSync(ANUNCIOS)) fs.writeFileSync(ANUNCIOS, '[]', 'utf8');

function leerJSON(ruta) {
    try { return JSON.parse(fs.readFileSync(ruta, 'utf8')); } catch(e) { return []; }
}
function leerP2P() { try { return JSON.parse(fs.readFileSync(P2P_FILE, 'utf8')); } catch(e) { return { ofertas: [], disputas: [], reputacion: {} }; } }
function guardarP2P(data) { fs.writeFileSync(P2P_FILE, JSON.stringify(data, null, 2), 'utf8'); }
function guardarJSON(ruta, datos) {
    fs.writeFileSync(ruta, JSON.stringify(datos, null, 2), 'utf8');
}

const CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
};

const server = http.createServer((req, res) => {
    if (req.method === 'OPTIONS') {
        res.writeHead(204, CORS);
        res.end();
        return;
    }

    if (req.method === 'GET' && req.url === '/productos') {
        res.writeHead(200, CORS);
        res.end(JSON.stringify(leerJSON(ARCHIVO)));
        return;
    }

    if (req.method === 'POST' && req.url === '/productos') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', () => {
            try {
                const nuevo = JSON.parse(body);
                nuevo.id = Date.now();
                nuevo.fecha = new Date().toISOString();
                const productos = leerJSON(ARCHIVO);
                productos.push(nuevo);
                guardarJSON(ARCHIVO, productos);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) {
                res.writeHead(400, CORS);
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    if (req.method === 'DELETE' && req.url.startsWith('/productos/')) {
        const id = parseInt(req.url.split('/')[2]);
        let productos = leerJSON(ARCHIVO);
        productos = productos.filter(p => p.id !== id);
        guardarJSON(ARCHIVO, productos);
        res.writeHead(200, CORS);
        res.end(JSON.stringify({ exito: true }));
        return;
    }

    if (req.method === 'POST' && req.url === '/quemar') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', () => {
            try {
                const tx = JSON.parse(body);
                tx.fecha = new Date().toISOString();
                const txs = leerJSON(TXS_FILE);
                txs.push(tx);
                guardarJSON(TXS_FILE, txs);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) {
                res.writeHead(400, CORS);
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    if (req.method === 'GET' && req.url === '/quemar') {
        res.writeHead(200, CORS);
        res.end(JSON.stringify(leerJSON(TXS_FILE)));
        return;
    }

    if (req.method === 'GET' && req.url === '/anuncios') {
        res.writeHead(200, CORS);
        res.end(JSON.stringify(leerJSON(ANUNCIOS)));
        return;
    }

    if (req.method === 'POST' && req.url === '/anuncios') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                if (data.admin !== 'drc_enviopactocunaaurorabaseritm') {
                    res.writeHead(403, CORS);
                    res.end(JSON.stringify({ error: 'No autorizado' }));
                    return;
                }
                const anuncios = leerJSON(ANUNCIOS);
                anuncios.unshift({ id: Date.now(), texto: data.texto, fecha: new Date().toISOString() });
                if (anuncios.length > 10) anuncios.pop();
                guardarJSON(ANUNCIOS, anuncios);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) {
                res.writeHead(400, CORS);
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    // ===== LOTERIA =====
    const LOTERIA_FILE = path.join(__dirname, "loteria.json");
    if (!fs.existsSync(LOTERIA_FILE)) {
        fs.writeFileSync(LOTERIA_FILE, JSON.stringify({ fondo: 0, boletos: [], historial: [], ultimoSorteo: null, anuncio: "🎰 La lotería es una herramienta de quema deflacionaria y crecimiento de la comunidad DirecCoin. El 10% de cada boleto se quema para siempre. ¡Invita usuarios, gana boletos gratis y haz crecer la red!" }, null, 2), "utf8");
    }
    function leerLoteria() {
        try { return JSON.parse(fs.readFileSync(LOTERIA_FILE, "utf8")); } catch(e) { return { fondo: 0, boletos: [], historial: [], ultimoSorteo: null }; }
    }
    function guardarLoteria(data) {
        fs.writeFileSync(LOTERIA_FILE, JSON.stringify(data, null, 2), "utf8");
    }

    // GET /loteria
    if (req.method === "GET" && req.url === "/loteria") {
        res.writeHead(200, CORS);
        res.end(JSON.stringify(leerLoteria()));
        return;
    }

    // POST /loteria/comprar
    if (req.method === "POST" && req.url === "/loteria/comprar") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const data = JSON.parse(body);
                if (!data.numeros || data.numeros.length !== 6) {
                    res.writeHead(400, CORS);
                    res.end(JSON.stringify({ error: "Debes elegir 6 números del 1 al 60" }));
                    return;
                }
                const loteria = leerLoteria();
                loteria.boletos.push({
                    id: Date.now(),
                    wallet: data.wallet,
                    numeros: data.numeros,
                    esGratis: data.esGratis || false,
                    fecha: new Date().toISOString()
                });
                if (!data.esGratis) loteria.fondo += 100;
                guardarLoteria(loteria);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true, mensaje: "✅ Boleto comprado. ¡Suerte el sábado!", totalBoletos: loteria.boletos.length, fondo: loteria.fondo }));
            } catch(e) {
                res.writeHead(400, CORS);
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    // POST /loteria/referido
    if (req.method === "POST" && req.url === "/loteria/referido") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const data = JSON.parse(body);
                const loteria = leerLoteria();
                loteria.boletos.push({
                    id: Date.now(),
                    wallet: data.referidor,
                    numeros: Array.from({length: 6}, () => Math.floor(Math.random() * 60) + 1),
                    esGratis: true,
                    fecha: new Date().toISOString()
                });
                loteria.boletos.push({
                    id: Date.now() + 1,
                    wallet: data.nuevo,
                    numeros: Array.from({length: 6}, () => Math.floor(Math.random() * 60) + 1),
                    esGratis: true,
                    fecha: new Date().toISOString()
                });
                guardarLoteria(loteria);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true, mensaje: "🎁 2 boletos gratis otorgados por referido" }));
            } catch(e) {
                res.writeHead(400, CORS);
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    
    // GET /p2p
    if (req.method === "GET" && req.url === "/p2p") {
        res.writeHead(200, CORS);
        res.end(JSON.stringify(leerP2P()));
        return;
    }

    // POST /p2p/crear
    if (req.method === "POST" && req.url === "/p2p/crear") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const d = JSON.parse(body);
                const p2p = leerP2P();
                p2p.ofertas.push({ id: Date.now(), vendedor: d.vendedor, cantidadDRC: d.cantidadDRC, precioFiat: d.precioFiat, monedaFiat: d.monedaFiat || "USD", metodoPago: d.metodoPago, contacto: d.contacto || "", estado: "activa", fecha: new Date().toISOString() });
                guardarP2P(p2p);
                res.writeHead(201, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) { res.writeHead(400, CORS); res.end(JSON.stringify({ error: e.message })); }
        });
        return;
    }

    // POST /p2p/comprar
    if (req.method === "POST" && req.url === "/p2p/comprar") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const d = JSON.parse(body);
                const p2p = leerP2P();
                const idx = p2p.ofertas.findIndex(o => o.id === d.ofertaId);
                if (idx !== -1 && p2p.ofertas[idx].estado === "activa") {
                    p2p.ofertas[idx].estado = "en_proceso";
                    p2p.ofertas[idx].comprador = d.comprador;
                    guardarP2P(p2p);
                }
                res.writeHead(200, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) { res.writeHead(400, CORS); res.end(JSON.stringify({ error: e.message })); }
        });
        return;
    }

    // POST /p2p/confirmar
    if (req.method === "POST" && req.url === "/p2p/confirmar") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const d = JSON.parse(body);
                const p2p = leerP2P();
                const idx = p2p.ofertas.findIndex(o => o.id === d.ofertaId);
                if (idx !== -1) {
                    p2p.ofertas[idx].estado = "completada";
                    if (!p2p.reputacion) p2p.reputacion = {};
                    if (!p2p.reputacion[p2p.ofertas[idx].vendedor]) p2p.reputacion[p2p.ofertas[idx].vendedor] = { ventas: 0, compras: 0, disputas: 0 };
                    p2p.reputacion[p2p.ofertas[idx].vendedor].ventas++;
                    guardarP2P(p2p);
                }
                res.writeHead(200, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) { res.writeHead(400, CORS); res.end(JSON.stringify({ error: e.message })); }
        });
        return;
    }

    // POST /p2p/disputa
    if (req.method === "POST" && req.url === "/p2p/disputa") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const d = JSON.parse(body);
                const p2p = leerP2P();
                const idx = p2p.ofertas.findIndex(o => o.id === d.ofertaId);
                if (idx !== -1) {
                    p2p.ofertas[idx].estado = "disputa";
                    p2p.disputas.push({ ofertaId: d.ofertaId, motivo: d.motivo, reportadoPor: d.reportadoPor, comprobante: d.comprobante || "", fecha: new Date().toISOString(), resuelta: false });
                    guardarP2P(p2p);
                }
                res.writeHead(200, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) { res.writeHead(400, CORS); res.end(JSON.stringify({ error: e.message })); }
        });
        return;
    }

    if (req.method === "POST" && req.url === "/loteria/actualizar") {
        let body = "";
        req.on("data", c => body += c);
        req.on("end", () => {
            try {
                const datos = JSON.parse(body);
                fs.writeFileSync(LOTERIA_FILE, JSON.stringify(datos, null, 2), "utf8");
                res.writeHead(200, CORS);
                res.end(JSON.stringify({ exito: true }));
            } catch(e) { res.writeHead(400, CORS); res.end(JSON.stringify({ error: e.message })); }
        });
        return;
    }
    res.writeHead(404, CORS);
    res.end(JSON.stringify({ error: 'No encontrado' }));
});

server.listen(PUERTO, '0.0.0.0', () => {
    console.log('🚀 Servidor activo en', PUERTO);
});
