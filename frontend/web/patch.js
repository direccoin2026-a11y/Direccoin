const fs = require('fs');
let file = fs.readFileSync('market_final.html', 'utf8');

// Reemplazar la función guardarProductos por una versión corregida
const nuevaGuardar = `    async function guardarProductos() {
        try {
            let gist = await fetch(\`https://api.github.com/gists/\${GIST_ID}\`).then(r => r.json());
            let actual = JSON.parse(gist.files['marketplace_direccoin.json']?.content || '{"productos":[]}');
            actual.productos = productosGlobal;
            await fetch(\`https://api.github.com/gists/\${GIST_ID}\`, {
                method: 'PATCH',
                headers: { 'Authorization': \`token \${GITHUB_TOKEN}\`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: { 'marketplace_direccoin.json': { content: JSON.stringify(actual, null, 2) } } })
            });
            return true;
        } catch(e) {
            console.error("Error guardando:", e);
            return false;
        }
    }`;

const viejaGuardar = /async function guardarProductos\(\) \{[\s\S]*?return false;\s*\}/;
file = file.replace(viejaGuardar, nuevaGuardar);

fs.writeFileSync('market_final.html', file);
console.log("✅ Parche aplicado. Recarga la página.");
