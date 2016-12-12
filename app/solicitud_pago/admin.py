from django.contrib import admin

from app.solicitud_pago.models import Contribuyente, ReferenciaPago, Banco, Convenio, Concepto, SalarioMinimo, SolicitudPago


class ContribuyenteAdmin(admin.ModelAdmin):
    model = Contribuyente
    list_display = ('nombre_completo', 'rfc', 'curp', 'entidad_federativa', 'municipio', 'localidad',)
    list_display_links = ('nombre_completo',)
    search_fields = ('nombre_completo', 'rfc', 'curp',)


class ReferenciaPagoAdmin(admin.ModelAdmin):
    model = ReferenciaPago
    list_display = ('referencia', 'vigencia', 'fecha_generacion',)
    search_fields = ('referencia',)
    ordering = ('fecha_generacion',)


class BancoAdmin(admin.ModelAdmin):
    model = Banco
    list_display = ('referencia', 'descripcion',)
    list_filter = ('referencia',)


class ConvenioAdmin(admin.ModelAdmin):
    model = Convenio
    list_display = ('banco', 'referencia', 'descripcion',)


class ConceptoAdmin(admin.ModelAdmin):
    model = Concepto
    list_display = ('clave', 'descripcion', 'salarios_minimos', 'get_convenios',)

    def get_convenios(self, obj):
        return " - ".join([c.referencia for c in obj.convenios.all()])

    get_convenios.short_description = "Convenios"


class SalarioMinimoAdmin(admin.ModelAdmin):
    model = SalarioMinimo
    list_display = ('monto', 'activo', 'fecha_alta', 'fecha_baja',)


class SolicitudPagoAdmin(admin.ModelAdmin):
    model = SolicitudPago
    list_display = ('contribuyente', 'concepto', 'salario_minimo', 'referencia_pago', 'fecha_solicitud', 'monto', 'descuento', 'deposito', 'total',)
    search_fields = ('contribuyente__nombre_completo', 'contribuyente__rfc', 'contribuyente__curp',)


admin.site.register(ReferenciaPago, ReferenciaPagoAdmin)
admin.site.register(Contribuyente, ContribuyenteAdmin)
admin.site.register(Banco, BancoAdmin)
admin.site.register(Convenio, ConvenioAdmin)
admin.site.register(Concepto, ConceptoAdmin)
admin.site.register(SalarioMinimo, SalarioMinimoAdmin)
admin.site.register(SolicitudPago, SolicitudPagoAdmin)
