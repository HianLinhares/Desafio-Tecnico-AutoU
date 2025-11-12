document.addEventListener('DOMContentLoaded', function() {
    const emailForm = document.getElementById('emailForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('resultsSection');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const categoryValue = document.getElementById('categoryValue');
    const responseValue = document.getElementById('responseValue');
    const processedText = document.getElementById('processedText');
    const categoryCard = document.getElementById('categoryCard');
    const responseCard = document.getElementById('responseCard');

    // Elementos dos inputs
    const emailTextArea = document.getElementById('emailText');
    const emailFileInput = document.getElementById('emailFile');

    // Event listener para o formulário
    emailForm.addEventListener('submit', function(e) {
        e.preventDefault();
        analyzeEmail();
    });

    // Event listener para novo análise - CORRIGIDO
    newAnalysisBtn.addEventListener('click', function() {
        resetForm();
        resultsSection.style.display = 'none';
        
        // ADICIONAR ESTAS LINHAS PARA REABILITAR OS INPUTS
        enableAllInputs();
    });

    // Função para analisar o email
    async function analyzeEmail() {
        const formData = new FormData(emailForm);
        
        // Validação
        const emailText = emailTextArea.value;
        const emailFile = emailFileInput.files[0];
        
        if (!emailText && !emailFile) {
            alert('Por favor, insira o texto do email ou faça upload de um arquivo.');
            return;
        }

        // Mostrar loading
        showLoading(true);

        try {
            const response = await fetch('/classify', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data);
            } else {
                throw new Error(data.error || 'Erro ao processar o email');
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao processar o email: ' + error.message);
        } finally {
            showLoading(false);
        }
    }

    // Função para exibir resultados
    function displayResults(data) {
        // Atualizar valores
        categoryValue.textContent = data.category;
        responseValue.textContent = data.response;
        processedText.textContent = data.processed_text;

        // Aplicar estilos baseados na categoria
        if (data.category === 'Produtivo') {
            categoryCard.classList.add('productive');
            categoryCard.classList.remove('unproductive');
            responseCard.classList.add('productive');
            responseCard.classList.remove('unproductive');
        } else {
            categoryCard.classList.add('unproductive');
            categoryCard.classList.remove('productive');
            responseCard.classList.add('unproductive');
            responseCard.classList.remove('productive');
        }

        // Mostrar seção de resultados
        resultsSection.style.display = 'block';
        
        // Scroll suave para os resultados
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Função para mostrar/ocultar loading
    function showLoading(show) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
        analyzeBtn.disabled = show;
    }

    // Função para resetar o formulário - CORRIGIDA
    function resetForm() {
        emailForm.reset();
        categoryCard.classList.remove('productive', 'unproductive');
        responseCard.classList.remove('productive', 'unproductive');
        
        // ADICIONAR: Reabilitar todos os inputs ao resetar
        enableAllInputs();
    }

    // NOVA FUNÇÃO: Reabilitar todos os inputs
    function enableAllInputs() {
        emailTextArea.disabled = false;
        emailFileInput.disabled = false;
        emailTextArea.placeholder = "Cole o texto do email aqui...";
    }

    // Validação em tempo real do textarea
    emailTextArea.addEventListener('input', function() {
        if (this.value.trim()) {
            emailFileInput.disabled = true;
            this.placeholder = "Texto do email (arquivo desabilitado)";
        } else {
            emailFileInput.disabled = false;
            this.placeholder = "Cole o texto do email aqui...";
        }
    });

    // Validação em tempo real do file input
    emailFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            emailTextArea.disabled = true;
            emailTextArea.placeholder = "Campo desabilitado (arquivo selecionado)";
        } else {
            emailTextArea.disabled = false;
            emailTextArea.placeholder = "Cole o texto do email aqui...";
        }
    });
});