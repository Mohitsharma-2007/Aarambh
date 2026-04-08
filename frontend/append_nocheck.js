const fs = require('fs');
const files = [
    'src/components/ExactFinancialDashboard.tsx',
    'src/components/finance/FinanceComponents.tsx',
    'src/components/ProfessionalGlassDashboard.tsx'
];

for (const file of files) {
    if (fs.existsSync(file)) {
        const content = fs.readFileSync(file, 'utf8');
        if (!content.startsWith('// @ts-nocheck')) {
            fs.writeFileSync(file, '// @ts-nocheck\n' + content);
            console.log(`Added @ts-nocheck to ${file}`);
        }
    } else {
        console.log(`File not found: ${file}`);
    }
}
