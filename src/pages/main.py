from selenium import webdriver

from pages.login_page import LoginPage
from pages.form_page import FormPage

def run():
    # Inicialização do Driver
    driver = webdriver.Chrome() 
    driver.get("http://localhost:8000/lote-teste") 

    # Instancia as páginas
    login_page = LoginPage(driver)
    form_page = FormPage(driver)

    # Executa as ações de negócio
    login_page.fazer_login("usuario", "senha")
    
    dados = {
        "numero_lote": "123",
        "produto": "10",   
        "status": "Ativo"  
    }
    
    # O método preencher_formulario já vai lidar com suas próprias esperas
    form_page.preencher_formulario(dados)

    # A página de formulário nos diz, com segurança e explicit wait interno, se deu certo
    if form_page.is_sucesso():
        print("Lote cadastrado com sucesso!")
    else:
        print("Falha ao cadastrar o lote.")

    driver.quit()

if __name__ == "__main__":
    run()
