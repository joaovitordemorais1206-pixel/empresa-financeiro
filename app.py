import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from dotenv import load_dotenv
from database import conectar, criar_banco_dados, inserir_dados_iniciais

load_dotenv()

app = Flask(__name__)


def buscar_grupos():
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, slug FROM grupos ORDER BY nome")
        grupos = cursor.fetchall()
        cursor.close()
        conexao.close()
        return grupos
    except psycopg2.Error as erro:
        print("Erro ao buscar grupos:", erro)
        return []


def buscar_grupo_por_slug(slug):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, slug FROM grupos WHERE slug = %s", (slug,))
        grupo = cursor.fetchone()
        cursor.close()
        conexao.close()
        return grupo
    except psycopg2.Error as erro:
        print("Erro ao buscar grupo:", erro)
        return None


def buscar_historico(grupo_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT h.id, h.data, h.descricao, g.nome
            FROM historicos h
            JOIN grupos g ON h.grupo_id = g.id
            WHERE h.grupo_id = %s
            ORDER BY h.data DESC
            """,
            (grupo_id,),
        )
        historico = cursor.fetchall()
        cursor.close()
        conexao.close()
        return historico
    except psycopg2.Error as erro:
        print("Erro ao buscar historico no banco de dados:", erro)
        return []


def buscar_historico_por_id(historico_id):
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, data, grupo_id, descricao FROM historicos WHERE id = %s", (historico_id,))
        item = cursor.fetchone()
        cursor.close()
        conexao.close()
        return item
    except psycopg2.Error as erro:
        print("Erro ao buscar historico:", erro)
        return None


@app.route("/")
def index():
    grupos = buscar_grupos()
    return render_template("index.html", grupos=grupos)


@app.route("/grupo/<slug>")
def grupo(slug):
    grupo = buscar_grupo_por_slug(slug)
    if not grupo:
        return "Grupo não encontrado", 404

    return render_template(
        "grupo.html",
        grupo_slug=grupo[2],
        grupo_nome=grupo[1],
    )


@app.route("/grupo/<slug>/historico")
def historico(slug):
    grupo = buscar_grupo_por_slug(slug)
    if not grupo:
        return "Grupo não encontrado", 404

    registros = buscar_historico(grupo[0])

    return render_template(
        "historico.html",
        grupo_slug=grupo[2],
        grupo_nome=grupo[1],
        historico=registros,
    )


@app.route("/grupo/<slug>/historico/adicionar", methods=["POST"])
def adicionar_historico(slug):
    grupo = buscar_grupo_por_slug(slug)
    if not grupo:
        return "Grupo não encontrado", 404

    data = request.form["data"]
    descricao = request.form["descricao"]

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO historicos (data, grupo_id, descricao) VALUES (%s, %s, %s)",
            (data, grupo[0], descricao),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
    except psycopg2.Error as erro:
        print("Erro ao adicionar historico:", erro)

    return redirect(url_for("historico", slug=slug))


@app.route("/grupo/<slug>/historico/editar/<int:historico_id>", methods=["GET", "POST"])
def editar_historico(slug, historico_id):
    grupo = buscar_grupo_por_slug(slug)
    if not grupo:
        return "Grupo não encontrado", 404

    if request.method == "POST":
        data = request.form["data"]
        descricao = request.form["descricao"]

        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE historicos SET data = %s, descricao = %s WHERE id = %s",
                (data, descricao, historico_id),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
        except psycopg2.Error as erro:
            print("Erro ao editar historico:", erro)

        return redirect(url_for("historico", slug=slug))

    item = buscar_historico_por_id(historico_id)
    registros = buscar_historico(grupo[0])

    return render_template(
        "historico.html",
        grupo_slug=grupo[2],
        grupo_nome=grupo[1],
        historico=registros,
        editando=item,
    )


@app.route("/grupo/<slug>/historico/remover/<int:historico_id>", methods=["POST"])
def remover_historico(slug, historico_id):
    grupo = buscar_grupo_por_slug(slug)
    if not grupo:
        return "Grupo não encontrado", 404

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM historicos WHERE id = %s", (historico_id,))
        conexao.commit()
        cursor.close()
        conexao.close()
    except psycopg2.Error as erro:
        print("Erro ao remover historico:", erro)

    return redirect(url_for("historico", slug=slug))


if __name__ == "__main__":
    criar_banco_dados()
    inserir_dados_iniciais()
    app.run(debug=True)
