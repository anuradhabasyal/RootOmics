#!/usr/bin/env python3
from io import StringIO, BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import pandas as pd
import mariadb

app = Flask(__name__)

def get_db_connection():
    return mariadb.connect(
        user='abasyal',
        password='anuradha',
        host='bioed-new.bu.edu',
        port=4253,
        database='Team13'
    )

def fetch_protein_data(filters):
    """
    Given a dict of filters, return (columns, results, all_ecs, pathway_ids).
    """
    # 1) Connect
    conn = get_db_connection()
    cursor = conn.cursor()

    # 2) Build & execute query
    query = """
        SELECT 
            p.Protein_name,
            p.Enzyme_Type,
            p.EC_numbers,
            p.KO_Numbers,
            p.GO_terms,
            GROUP_CONCAT(DISTINCT pw.KEGG_pathway) AS Pathways,
            GROUP_CONCAT(DISTINCT pw.CAZyme_class_superfamily) AS CAZyme_Classes,
            GROUP_CONCAT(DISTINCT ep.Broad_Process) AS Ecosystem_Processes
        FROM Proteins p
        LEFT JOIN Protein_Pathway pp ON p.PID = pp.PID
        LEFT JOIN Pathways pw ON pp.PAID = pw.PAID
        LEFT JOIN Protein_Ecosystem_Process pep ON p.PID = pep.PID
        LEFT JOIN Ecosystem_Processes ep ON pep.EID = ep.EID
        WHERE (? = '' OR p.Protein_name   LIKE CONCAT('%', ?, '%'))
          AND (? = '' OR p.Enzyme_Type    LIKE CONCAT('%', ?, '%'))
          AND (? = '' OR p.EC_numbers     LIKE CONCAT('%', ?, '%'))
          AND (? = '' OR p.KO_Numbers     LIKE CONCAT('%', ?, '%'))
          AND (? = '' OR p.GO_terms       LIKE CONCAT('%', ?, '%'))
          AND (? = '' OR pw.KEGG_pathway  LIKE CONCAT('%', ?, '%'))
        GROUP BY p.PID
    """
    params = (
        filters['name'], filters['name'],
        filters['enzyme_type'], filters['enzyme_type'],
        filters['ec'], filters['ec'],
        filters['ko'], filters['ko'],
        filters['go'], filters['go'],
        filters['kegg'], filters['kegg'],
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    # 3) Process rows into dicts & collect ECs
    results = []
    all_ecs = set()
    for r in rows:
        d = dict(zip(columns, r))
        d['Pathways'] = d.get('Pathways', '').split(',') if d.get('Pathways') else []
        d['Ecosystem_Processes'] = (
            d.get('Ecosystem_Processes', '').split(',')
            if d.get('Ecosystem_Processes') else []
        )
        results.append(d)

        for ec in (d.get('EC_numbers') or '').split(','):
            ec = ec.strip()
            if ec:
                all_ecs.add(ec)
    
    # Get lists of protein names and enzyme types for autocomplete
    cursor.execute("SELECT DISTINCT Protein_name FROM Proteins ORDER BY Protein_name")
    protein_names = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT Enzyme_Type FROM Proteins ORDER BY Enzyme_Type")
    enzyme_types = [row[0] for row in cursor.fetchall()]
    
    conn.close()

    # 4) Define which KEGG maps to show
    pathway_ids = {
        'Glycolysis / Gluconeogenesis': '00010',
        'Nitrogen metabolism':          '00910',
        'TCA cycle':                    '00020',
    }

    return columns, results, sorted(all_ecs), pathway_ids, protein_names, enzyme_types

# Redirect root to /introduction
@app.route('/')
def index():
    return redirect(url_for('introduction'))

@app.route('/introduction')
def introduction():
    return render_template('app.html', active_tab='introduction', active_tab_title='Introduction')

@app.route('/explorer')
def explorer():
    # Gather filters from query string
    filters = {
        'name':        request.args.get('name', ''),
        'enzyme_type': request.args.get('enzyme_type', ''),
        'ec':          request.args.get('ec', ''),
        'ko':          request.args.get('ko', ''),
        'go':          request.args.get('go', ''),
        'kegg':        request.args.get('kegg', ''),
    }
    
    # Get autocomplete data for initial page load
    _, _, _, _, protein_names, enzyme_types = fetch_protein_data({'name': '', 'enzyme_type': '', 'ec': '', 'ko': '', 'go': '', 'kegg': ''})
    
    # Pass to template
    return render_template(
        'app.html',
        active_tab='explorer',
        active_tab_title='Explorer',
        results=None,  # Initial load has no results, will be populated by AJAX
        highlighted_ecs="",
        pathway_ids={},
        protein_names=protein_names,
        enzyme_types=enzyme_types,
        filters=filters
    )

@app.route('/proteins')
def proteins():
    # Redirect to explorer for backward compatibility
    return redirect(url_for('explorer', **request.args))

@app.route('/download_page')
def download_page():
    # Gather filters from query string (maintain any active filters)
    filters = {
        'name':        request.args.get('name', ''),
        'enzyme_type': request.args.get('enzyme_type', ''),
        'ec':          request.args.get('ec', ''),
        'ko':          request.args.get('ko', ''),
        'go':          request.args.get('go', ''),
        'kegg':        request.args.get('kegg', ''),
    }
    
    return render_template('app.html', active_tab='download', active_tab_title='Download', filters=filters)

@app.route('/contact')
def contact():
    return render_template('app.html', active_tab='contact', active_tab_title='Contact')

@app.route('/help_page')
def help_page():
    return render_template('app.html', active_tab='help', active_tab_title='Help')

@app.route('/search_data')
def search_data():
    """AJAX endpoint to get search results"""
    # Get filters from query parameters
    filters = {
        'name':        request.args.get('name', ''),
        'enzyme_type': request.args.get('enzyme_type', ''),
        'ec':          request.args.get('ec', ''),
        'ko':          request.args.get('ko', ''),
        'go':          request.args.get('go', ''),
        'kegg':        request.args.get('kegg', ''),
    }
    
    # Fetch filtered data
    _, results, all_ecs, pathway_ids, _, _ = fetch_protein_data(filters)
    
    # Return JSON-formatted results
    return jsonify({
        'results': results,
        'highlighted_ecs': ",".join(all_ecs),
        'pathway_ids': pathway_ids
    })

@app.route('/get_suggestions', methods=['GET'])
def get_suggestions():
    """AJAX endpoint to get protein name or enzyme type suggestions"""
    field = request.args.get('field', '')
    query = request.args.get('query', '')
    
    if not field or not query:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if field == 'protein_name':
        sql = "SELECT DISTINCT Protein_name FROM Proteins WHERE Protein_name LIKE ? ORDER BY Protein_name LIMIT 10"
    elif field == 'enzyme_type':
        sql = "SELECT DISTINCT Enzyme_Type FROM Proteins WHERE Enzyme_Type LIKE ? ORDER BY Enzyme_Type LIMIT 10"
    else:
        return jsonify([])
    
    cursor.execute(sql, (f"%{query}%",))
    suggestions = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(suggestions)

@app.route('/download_data')
def download_data():
    # 1) Gather filters
    filters = {
        'name':        request.args.get('name', ''),
        'enzyme_type': request.args.get('enzyme_type', ''),
        'ec':          request.args.get('ec', ''),
        'ko':          request.args.get('ko', ''),
        'go':          request.args.get('go', ''),
        'kegg':        request.args.get('kegg', ''),
    }

    # 2) Fetch filtered data (reuse your existing helper)
    _, results, _, _, _, _ = fetch_protein_data(filters)

    # 3) Build DataFrame
    df = pd.DataFrame([
        {
            col: (",".join(val) if isinstance(val, list) else val)
            for col, val in row.items()
        }
        for row in results
    ])

    # 4) Decide format
    fmt = request.args.get('fmt', 'csv').lower()

    if fmt == 'xlsx':
        # Excel export
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Proteins')
            writer.save()
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name='rootomics_proteins.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    else:
        # CSV export
        si = StringIO()
        df.to_csv(si, index=False)
        csv_bytes = si.getvalue().encode('utf-8')
        bio = BytesIO(csv_bytes)
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name='rootomics_proteins.csv',
            mimetype='text/csv'
        )

if __name__ == '__main__':
    app.run(debug=True)
