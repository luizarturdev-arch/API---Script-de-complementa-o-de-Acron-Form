import io
import json
from flask import Flask, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from flask_cors import CORS

# --- Inicialização do Servidor ---
app = Flask(__name__)
CORS(app)

# O endpoint que o seu frontend irá chamar (POST /api/preencher-pdf)
@app.route('/api/preencher-pdf', methods=['POST'])
def preencher_pdf():
    # 1. Verificar se o arquivo PDF e os dados estão presentes no request
    if 'pdf_file' not in request.files or 'dados_cliente' not in request.form:
        return jsonify({"erro": "Requisição incompleta. Arquivo PDF e dados de cliente são necessários."}), 400

    pdf_file = request.files['pdf_file']
    dados_json = request.form['dados_cliente']

    try:
        # Converter a string JSON dos dados para um dicionário Python
        dados_originais = json.loads(dados_json)
    except json.JSONDecodeError:
        return jsonify({"erro": "Formato de dados do cliente inválido (não é JSON válido)."}), 400

    # 2. Ler o PDF do buffer de memória (sem salvar no disco)
    try:
        # pdf_file.stream é um objeto de arquivo (file-like object)
        reader = PdfReader(pdf_file.stream)
        writer = PdfWriter()
        writer.append(reader)
        
        # --- Lógica de Mapeamento de Campos (Adaptada do seu script) ---
        dados_expandidos = {}
        campos_disponiveis = reader.get_fields().keys()

        # Itera sobre os dados únicos e mapeia para todas as variações de campos no PDF
        for nome_desejado, valor in dados_originais.items():
            for campo_pdf in campos_disponiveis:
                if campo_pdf.startswith(nome_desejado):
                    dados_expandidos[campo_pdf] = valor
        # -----------------------------------------------------------------

        # 3. Preencher o formulário em todas as páginas
        for page in writer.pages:
            writer.update_page_form_field_values(
                page, 
                dados_expandidos
            )

        # 4. Salvar o PDF processado em um buffer de memória
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0) # Retorna ao início do buffer para leitura

        # 5. Enviar o arquivo de volta para o frontend
        return send_file(
            output_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='formulario_preenchido.pdf'
        )

    except Exception as e:
        # Captura qualquer erro inesperado durante o processamento
        return jsonify({"erro": f"Erro interno ao processar o PDF: {str(e)}"}), 500

# Permite rodar o servidor
if __name__ == '__main__':
    # Em produção, você usaria um servidor WSGI (Gunicorn/uWSGI)
    app.run(debug=True, port=5000)