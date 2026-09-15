#!/bin/bash

# Script para facilitar a execução de testes do Comercializa

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para printar com cor
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Checkar se está na pasta certa
if [ ! -f "manage.py" ]; then
    echo "Erro: Execute este script a partir da pasta backend/"
    echo "cd backend && ./run_tests.sh"
    exit 1
fi

# Ativar venv se não estiver ativado
if [ -z "$VIRTUAL_ENV" ]; then
    print_info "Ativando virtual environment..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        print_info "Criando virtual environment..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -q -r requirements.txt
    fi
fi

print_header "Testes Automatizados - Comercializa"

case "${1:-all}" in
    all)
        print_info "Rodando todos os testes..."
        pytest tests/ -v
        ;;
    quick)
        print_info "Rodando testes rápidos (sem cobertura)..."
        pytest tests/ -q
        ;;
    coverage)
        print_info "Rodando com relatório de cobertura..."
        pytest tests/ --cov=core --cov-report=html --cov-report=term-missing
        print_success "Relatório gerado em htmlcov/index.html"
        ;;
    models)
        print_info "Rodando testes unitários..."
        pytest tests/test_models.py -v
        ;;
    api)
        print_info "Rodando testes de integração..."
        pytest tests/test_api.py -v
        ;;
    sad)
        print_info "Rodando testes do SAD..."
        pytest tests/test_sad.py -v
        ;;
    acceptance)
        print_info "Rodando testes de aceitação..."
        pytest tests/test_acceptance.py -v
        ;;
    watch)
        print_info "Modo watch (roda testes a cada mudança)..."
        print_info "Instale com: pip install pytest-watch"
        ptw tests/
        ;;
    failed)
        print_info "Rerodando apenas testes que falharam..."
        pytest tests/ --lf -v
        ;;
    last)
        print_info "Rodando último teste que foi executado..."
        pytest tests/ --ff -v
        ;;
    *)
        echo "Uso: ./run_tests.sh [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  all         - Rodar todos os testes (padrão)"
        echo "  quick       - Rodar rápido sem cobertura"
        echo "  coverage    - Rodar com cobertura HTML"
        echo "  models      - Rodar testes unitários"
        echo "  api         - Rodar testes de integração"
        echo "  sad         - Rodar testes do SAD"
        echo "  acceptance  - Rodar testes de aceitação"
        echo "  watch       - Modo watch (requer pytest-watch)"
        echo "  failed      - Rodar apenas testes que falharam"
        echo "  last        - Rodar último teste"
        exit 1
        ;;
esac

print_success "Pronto!"
