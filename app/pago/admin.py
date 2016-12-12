from django.contrib import admin

from actions import export_as_csv
from app.pago.models import ReporteDeposito, Deposito


class ReporteDepositoAdmin(admin.ModelAdmin):
    model = ReporteDeposito
    list_display = ('nombre_original', 'banco', 'depositos_reportados', 'depositos_procesados', 'fecha_carga', 'hash_contenido',)
    list_filter = ['fecha_carga']
    list_display_links = ['nombre_original']
    search_fields = ('banco__referencia', )


class DepositoAdmin(admin.ModelAdmin):
    model = Deposito
    list_display = ('referencia', 'fecha', 'abono', 'saldo', 'cargo', 'reporte_deposito',)
    search_fields = ['referencia']
    list_display_links = ('referencia',)
    actions = [export_as_csv]


admin.site.register(ReporteDeposito, ReporteDepositoAdmin)
admin.site.register(Deposito, DepositoAdmin)
