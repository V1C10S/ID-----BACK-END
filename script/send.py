# ======================================================== #
# SCRIPT :: send.py                                        # 
# PROPÓSITO: enviar um único e-mail HTML (teste de SMTP)   #     
# POR QUE EXISTE AQUI:                                     # 
# - Testar credenciais SMTP rapidamente                    # 
# - Verificar renderização do HTML no cliente              #     
# COMO USAR:                                               # 
#   python send.py                                         #     
# NOTAS:                                                   # 
# - Usa Flask-Mail localmente (sem rodar o servidor)       # 
# - Destinatário e conteúdo estão hardcoded para debug     # 
# STATUS: utilitário de suporte (não é parte da API)       #    
# ======================================================== #


from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='aetherdigital.sev@gmail.com',
    MAIL_PASSWORD='wegpfourblzpfmug',  
    MAIL_DEFAULT_SENDER=('Aether Digital', 'aetherdigital.sev@gmail.com'),
)

mail = Mail(app)


def send_email(to: str, subject: str, html: str):
    msg = Message(subject=subject, recipients=[to], html=html)
    mail.send(msg)
    print(f"✅ Email enviado para {to}")


if __name__ == "__main__":
    with app.app_context():
        send_email(
            to="viitts.152@gmail.com",
            subject="Teste 01",
            html="<b>Se chegou, o envio está funcionando!</b>",
        )
