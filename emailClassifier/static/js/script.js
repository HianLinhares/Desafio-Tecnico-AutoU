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

    // Event listener para o formulário
    emailForm.addEventListener('submit', function(e) {
        e.preventDefault();
        analyzeEmail();
    });

    // Event listener para novo análise
    newAnalysisBtn.addEventListener('click', function() {
        resetForm();
        resultsSection.style.display = 'none';
    });

    // Função para analisar o email
    async function analyzeEmail() {
        const formData = new FormData(emailForm);
        
        // Validação
        const emailText = document.getElementById('emailText').value;
        const emailFile = document.getElementById('emailFile').files[0];
        
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

    // Função para resetar o formulário
    function resetForm() {
        emailForm.reset();
        categoryCard.classList.remove('productive', 'unproductive');
        responseCard.classList.remove('productive', 'unproductive');
    }

    // Validação em tempo real do textarea
    const emailTextArea = document.getElementById('emailText');
    emailTextArea.addEventListener('input', function() {
        if (this.value.trim()) {
            document.getElementById('emailFile').disabled = true;
        } else {
            document.getElementById('emailFile').disabled = false;
        }
    });

    // Validação em tempo real do file input
    const emailFileInput = document.getElementById('emailFile');
    emailFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            document.getElementById('emailText').disabled = true;
        } else {
            document.getElementById('emailText').disabled = false;
        }
    });
});