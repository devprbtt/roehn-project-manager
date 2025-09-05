// Funções utilitárias para toda a aplicação
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar classe active ao item de menu atual
    const currentLocation = location.href;
    const menuItems = document.querySelectorAll('.nav-link');
    const menuLength = menuItems.length;
    
    for (let i = 0; i < menuLength; i++) {
        if (menuItems[i].href === currentLocation) {
            menuItems[i].classList.add('active');
        }
    }
    
    // REMOVER ESTA PARTE (causa duplicação de confirmações)
    // // Adicionar confirmção para ações de exclusão
    // const deleteButtons = document.querySelectorAll('.btn-danger');
    // deleteButtons.forEach(button => {
    //     button.addEventListener('click', function(e) {
    //         if (!confirm('Tem certeza que deseja excluir este item?')) {
    //             e.preventDefault();
    //         }
    //     });
    // });
});

// Função para exibir mensagens de alerta
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}