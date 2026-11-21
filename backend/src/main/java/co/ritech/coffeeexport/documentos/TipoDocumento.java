package co.ritech.coffeeexport.documentos;

import java.util.List;

public enum TipoDocumento {
    CERTIFICADO_ORIGEN("Certificado de origen"), FITOSANITARIO("Certificado fitosanitario"), FACTURA_COMERCIAL("Factura comercial"),
    LISTA_EMPAQUE("Lista de empaque"), DECLARACION_ADUANERA("Declaración aduanera"), OTRO("Otro");

    /** RF-21, RR-06: sin estos cuatro la exportación no puede pasar a En tránsito. */
    public static final List<TipoDocumento> OBLIGATORIOS = List.of(CERTIFICADO_ORIGEN, FITOSANITARIO, FACTURA_COMERCIAL, DECLARACION_ADUANERA);

    private final String etiqueta;

    TipoDocumento(String etiqueta) {
        this.etiqueta = etiqueta;
    }

    public String getEtiqueta() {
        return etiqueta;
    }
}
