const fs = require('fs');
const path = require('path');

const LOTERIA = path.join(__dirname, 'frontend', 'web', 'loteria.json');

function leerLoteria() { try { return JSON.parse(fs.readFileSync(LOTERIA, 'utf8')); } catch(e) { return null; } }
function guardarLoteria(data) { fs.writeFileSync(LOTERIA, JSON.stringify(data, null, 2), 'utf8'); }

function sortear() {
    const data = leerLoteria();
    if (!data) { console.log('❌ No se pudo leer loteria.json'); return; }
    if (data.boletos.length === 0) { console.log('🎰 Sin boletos esta semana.'); return; }

    const ganadores = [];
    while (ganadores.length < 6) {
        const n = Math.floor(Math.random() * 60) + 1;
        if (!ganadores.includes(n)) ganadores.push(n);
    }
    ganadores.sort((a, b) => a - b);
    console.log('🎯 Números ganadores:', ganadores.join(', '));

    const fondo = data.fondo || 0;
    const premio6 = Math.floor(fondo * 0.70);
    const premio5 = Math.floor(fondo * 0.15);
    const premio4 = Math.floor(fondo * 0.05);
    const quemado = Math.floor(fondo * 0.10);

    let ganador6 = null, ganador5 = null, ganador4 = null;

    for (const boleto of data.boletos) {
        if (boleto.sorteado) continue;
        const aciertos = boleto.numeros.filter(n => ganadores.includes(n)).length;
        if (aciertos === 6 && !ganador6) ganador6 = boleto;
        else if (aciertos === 5 && !ganador5) ganador5 = boleto;
        else if (aciertos === 4 && !ganador4) ganador4 = boleto;
    }

    console.log(`💰 Fondo: ${fondo.toLocaleString()} DRC`);
    console.log(`🔥 Quemados: ${quemado.toLocaleString()} DRC`);
    if (ganador6) console.log(`🏆 6 aciertos (70%): ${ganador6.wallet} → ${premio6.toLocaleString()} DRC`);
    if (ganador5) console.log(`🥈 5 aciertos (15%): ${ganador5.wallet} → ${premio5.toLocaleString()} DRC`);
    if (ganador4) console.log(`🥉 4 aciertos (5%): ${ganador4.wallet} → ${premio4.toLocaleString()} DRC`);
    if (!ganador6 && !ganador5 && !ganador4) console.log('😞 Nadie acertó. El fondo se acumula.');

    data.boletos = data.boletos.map(b => {
        const aciertos = b.numeros.filter(n => ganadores.includes(n)).length;
        const gano = (aciertos === 6 && ganador6 && b.id === ganador6.id) ||
                     (aciertos === 5 && ganador5 && b.id === ganador5.id) ||
                     (aciertos === 4 && ganador4 && b.id === ganador4.id);
        return { ...b, sorteado: true, aciertos, gano };
    });

    if (!data.historial) data.historial = [];
    data.historial.push({
        fecha: new Date().toISOString(),
        numerosGanadores: ganadores,
        fondo, premio6, premio5, premio4, quemado,
        ganador6: ganador6 ? ganador6.wallet : null,
        ganador5: ganador5 ? ganador5.wallet : null,
        ganador4: ganador4 ? ganador4.wallet : null
    });

    data.ultimoSorteo = new Date().toISOString();
    if (ganador6 || ganador5 || ganador4) data.fondo = 0;
    guardarLoteria(data);
    console.log('✅ Sorteo completado.');
}

sortear();
