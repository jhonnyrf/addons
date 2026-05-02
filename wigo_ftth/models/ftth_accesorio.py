# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)


class FtthAccesorio(models.Model):
    """Catálogo de accesorios utilizados en instalaciones FTTH."""
    _name = 'ftth.accesorio'
    _description = 'Accesorio FTTH'
    _rec_name= 'name'
    _order = 'name'

    # ==========================================================================
    # Fields
    # ==========================================================================
    name = fields.Char(
        string='Nombre',
        required=True,
        index=True,
    )

    codigo = fields.Char(
        string='Código',
        copy=False,
        help='Código único del accesorio (SKU)',
    )

    tipo_unidad = fields.Selection(
        [
            ('m', 'Metros'),
            ('unidad', 'Unidad'),
        ],
        string='Tipo de unidad',
        required=True,
        default='unidad',
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    notas = fields.Html(
        string='Notas',
    )

    # Stock relacionado (relación inversa)
    stock_id = fields.One2many(
        'ftth.stock.accesorio',
        'accesorio_id',
        string='Stock',
        readonly=True,
    )

    # Cantidad disponible (campo computed a partir del stock)
    cantidad_disponible = fields.Float(
        string='Cantidad disponible',
        compute='_compute_cantidad_disponible',
        inverse='_inverse_cantidad_disponible',
        store=True,
    )

    # Movimientos (relación inversa)
    movimiento_ids = fields.One2many(
        'ftth.movimiento.accesorio',
        'accesorio_id',
        string='Historial de movimientos',
        readonly=True,
    )

    # ==========================================================================
    # Constraints
    # ==========================================================================
    _sql_constraints = [
        ('codigo_uniq', 'UNIQUE(codigo)', 'El código del accesorio debe ser único.'),
        ('name_uniq', 'UNIQUE(name)', 'El nombre del accesorio debe ser único.'),
    ]

    # ==========================================================================
    # Computed Fields
    # ==========================================================================
    @api.depends('stock_id.cantidad_disponible')
    def _compute_cantidad_disponible(self):
        """Obtiene la cantidad disponible del registro de stock asociado."""
        for record in self:
            if record.stock_id:
                record.cantidad_disponible = record.stock_id[0].cantidad_disponible
            else:
                record.cantidad_disponible = 0.0

    def _inverse_cantidad_disponible(self):
        """Cuando se edita `cantidad_disponible` en el accesorio, propagar al stock.

        Usa el método `ajustar_stock` para registrar movimientos.
        """
        for record in self:
            cantidad = record.cantidad_disponible or 0.0
            stock = record.stock_id[:1]
            if stock:
                try:
                    stock.ajustar_stock(cantidad, referencia='Ajuste desde accesorio')
                except Exception:
                    _logger.exception('Error al ajustar stock desde accesorio %s', record.id)
            else:
                try:
                    self.env['ftth.stock.accesorio'].create({
                        'accesorio_id': record.id,
                        'cantidad_disponible': cantidad,
                    })
                except Exception:
                    _logger.exception('Error al crear stock inicial para accesorio %s', record.id)

    # ==========================================================================
    # ORM Overrides
    # ==========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Crea accesorios y automáticamente un registro de stock para cada uno.

        Si no se provee `codigo`, intenta obtenerlo desde una secuencia
        (`ir.sequence`). Si no existe, genera un fallback a partir del nombre
        o con un timestamp UTC para asegurar unicidad.
        """
        for vals in vals_list:
            if not vals.get('codigo'):
                try:
                    vals['codigo'] = self.env['ir.sequence'].next_by_code('ftth.accesorio')
                except Exception:
                    if vals.get('name'):
                        base = re.sub(r"[^A-Z0-9]", "", vals.get('name', '').upper())[:10]
                        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                        vals['codigo'] = f"{base}-{ts}"
                    else:
                        vals['codigo'] = f"ACC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        records = super().create(vals_list)
        for record in records:
            # Crear automáticamente el registro de stock si no existe
            if not record.stock_id:
                self.env['ftth.stock.accesorio'].create({
                    'accesorio_id': record.id,
                    'cantidad_disponible': 0.0,
                })
        # Asegurar que `codigo` esté persistido (por si el cliente no lo envió)
        for record in records:
            if not record.codigo:
                try:
                    codigo = self.env['ir.sequence'].next_by_code('ftth.accesorio')
                except Exception:
                    if record.name:
                        base = re.sub(r"[^A-Z0-9]", "", record.name.upper())[:10]
                        codigo = f"{base}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    else:
                        codigo = f"ACC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                try:
                    record.write({'codigo': codigo})
                except Exception:
                    _logger.exception('No se pudo escribir codigo para accesorio %s', record.id)
        return records

    @api.model
    def default_get(self, fields_list):
        """Proveer un `codigo` por defecto al abrir el formulario 'Nuevo'."""
        res = super().default_get(fields_list)
        if 'codigo' in fields_list and not res.get('codigo'):
            try:
                res['codigo'] = self.env['ir.sequence'].next_by_code('ftth.accesorio')
            except Exception:
                res['codigo'] = f"ACC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return res

    @api.onchange('name')
    def _onchange_name_generate_codigo(self):
        """Genera automáticamente `codigo` al escribir el nombre si está vacío.

        Esto permite que el código sea visible en el formulario antes de guardar.
        """
        if not self.name:
            return
        if self.codigo:
            return
        try:
            seq = self.env['ir.sequence'].next_by_code('ftth.accesorio')
            if seq:
                self.codigo = seq
                return
        except Exception:
            pass
        base = re.sub(r"[^A-Z0-9]", "", self.name.upper())[:10]
        self.codigo = f"{base}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # ==========================================================================
    # Display
    # ==========================================================================
    def name_get(self):
        """Muestra nombre + código en las vistas."""
        result = []
        for record in self:
            name = record.name
            if record.codigo:
                name = f"{record.codigo} - {record.name}"
            result.append((record.id, name))
        return result


class FtthStockAccesorio(models.Model):
    """Control de stock de accesorios."""
    _name = 'ftth.stock.accesorio'
    _description = 'Stock de Accesorio'
    _rec_name= 'accesorio_id'
    

    # ==========================================================================
    # Fields
    # ==========================================================================
    accesorio_id = fields.Many2one(
        'ftth.accesorio',
        string='Accesorio',
        required=True,
        ondelete='cascade',
        index=True,
    )

    cantidad_disponible = fields.Float(
        string='Cantidad disponible',
        default=0.0,
        required=True,
    )

    unidad = fields.Selection(
        [
            ('m', 'Metros'),
            ('unidad', 'Unidad'),
        ],
        string='Unidad',
        related='accesorio_id.tipo_unidad',
        store=True,
        readonly=True,
    )

    fecha_actualizacion = fields.Datetime(
        string='Fecha de actualización',
        default=fields.Datetime.now,
        readonly=True,
    )

    # Movimientos relacionados (a través del accesorio)
    movimiento_ids = fields.One2many(
        related='accesorio_id.movimiento_ids',
        readonly=True,
    )

    # ==========================================================================
    # Constraints
    # ==========================================================================
    _sql_constraints = [
        ('accesorio_id_uniq', 'UNIQUE(accesorio_id)', 'Solo puede haber un registro de stock por accesorio.'),
    ]

    # ==========================================================================
    # Validations
    # ==========================================================================
    @api.constrains('cantidad_disponible')
    def _check_cantidad_no_negativa(self):
        """Valida que la cantidad disponible no sea negativa."""
        for record in self:
            if record.cantidad_disponible < 0:
                raise ValidationError(
                    f"La cantidad disponible de '{record.accesorio_id.name}' no puede ser negativa. "
                    f"Stock actual: {record.cantidad_disponible}"
                )

    # ==========================================================================
    # ORM Overrides
    # ==========================================================================
    def write(self, vals):
        """Actualiza la fecha de actualización cuando cambia cantidad."""
        if 'cantidad_disponible' in vals:
            vals['fecha_actualizacion'] = fields.Datetime.now()
        return super().write(vals)

    # ==========================================================================
    # Public Methods
    # ==========================================================================
    def aumentar_stock(self, cantidad, referencia=''):
        """Aumenta el stock (entrada) y registra movimiento."""
        self.ensure_one()
        if cantidad <= 0:
            raise ValidationError('La cantidad a aumentar debe ser mayor a 0.')

        self.cantidad_disponible += cantidad
        
        # Registrar movimiento sin disparar actualización de stock (evitar ciclo)
        self.env['ftth.movimiento.accesorio'].with_context(skip_stock_update=True).create({
            'accesorio_id': self.accesorio_id.id,
            'tipo_movimiento': 'entrada',
            'cantidad': cantidad,
            'referencia': referencia,
        })

        return True

    def disminuir_stock(self, cantidad, referencia=''):
        """Disminuye el stock (salida) y registra movimiento. Valida stock suficiente."""
        self.ensure_one()
        if cantidad <= 0:
            raise ValidationError('La cantidad a disminuir debe ser mayor a 0.')

        if self.cantidad_disponible < cantidad:
            raise ValidationError(
                f"Stock insuficiente de '{self.accesorio_id.name}'. "
                f"Disponible: {self.cantidad_disponible}, Solicitado: {cantidad}"
            )

        self.cantidad_disponible -= cantidad

        # Registrar movimiento sin disparar actualización de stock (evitar ciclo)
        self.env['ftth.movimiento.accesorio'].with_context(skip_stock_update=True).create({
            'accesorio_id': self.accesorio_id.id,
            'tipo_movimiento': 'salida',
            'cantidad': cantidad,
            'referencia': referencia,
        })

        return True

    def ajustar_stock(self, cantidad_nueva, referencia=''):
        """Ajusta el stock a una cantidad específica (corrección manual)."""
        self.ensure_one()
        if cantidad_nueva < 0:
            raise ValidationError('La cantidad no puede ser negativa.')

        diferencia = cantidad_nueva - self.cantidad_disponible
        self.cantidad_disponible = cantidad_nueva

        # Registrar movimiento de ajuste sin disparar actualización de stock (evitar ciclo)
        self.env['ftth.movimiento.accesorio'].with_context(skip_stock_update=True).create({
            'accesorio_id': self.accesorio_id.id,
            'tipo_movimiento': 'ajuste',
            'cantidad': diferencia,
            'referencia': referencia,
        })

        return True


class FtthMovimientoAccesorio(models.Model):
    """Historial de movimientos de accesorios."""
    _name = 'ftth.movimiento.accesorio'
    _description = 'Movimiento de Accesorio'
    _rec_name= 'accesorio_id'    
    _order = 'fecha DESC'

    # ==========================================================================
    # Fields
    # ==========================================================================
    accesorio_id = fields.Many2one(
        'ftth.accesorio',
        string='Accesorio',
        required=True,
        ondelete='cascade',
        index=True,
    )

    tipo_movimiento = fields.Selection(
        [
            ('entrada', 'Entrada (Compra/Devolución)'),
            ('salida', 'Salida (Instalación/Uso)'),
            ('ajuste', 'Ajuste (Corrección)'),
        ],
        string='Tipo de movimiento',
        required=True,
        index=True,
    )

    cantidad = fields.Float(
        string='Cantidad',
        required=True,
    )

    fecha = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )

    referencia = fields.Char(
        string='Referencia / Motivo',
        help='Documento o motivo asociado (ej: OC-001, Inst-2026-05-001)',
    )

    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        default=lambda self: self.env.user,
        readonly=True,
    )

    # ==========================================================================
    # Constraints
    # ==========================================================================
    @api.constrains('cantidad')
    def _check_cantidad_no_cero(self):
        """Valida que la cantidad no sea cero."""
        for record in self:
            if record.cantidad == 0:
                raise ValidationError('La cantidad no puede ser cero.')

    # ==========================================================================
    # ORM Overrides
    # ==========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Crea movimientos y actualiza el stock automáticamente.
        
        Si el contexto tiene 'skip_stock_update=True', no actualiza el stock
        (esto lo usan los métodos aumentar_stock, disminuir_stock, ajustar_stock).
        """
        records = super().create(vals_list)
        
        # Si se debe omitir la actualización (porque fue creado por métodos de stock), retorna
        if self.env.context.get('skip_stock_update'):
            return records
        
        # Actualizar stock para cada movimiento creado manualmente
        for record in records:
            stock = self.env['ftth.stock.accesorio'].search([
                ('accesorio_id', '=', record.accesorio_id.id)
            ], limit=1)
            
            if not stock:
                _logger.warning('No se encontró stock para accesorio %s', record.accesorio_id.id)
                continue
            
            try:
                if record.tipo_movimiento == 'entrada':
                    # Entrada: aumentar stock
                    stock.cantidad_disponible += record.cantidad
                elif record.tipo_movimiento == 'salida':
                    # Salida: disminuir stock
                    if stock.cantidad_disponible < record.cantidad:
                        raise ValidationError(
                            f"Stock insuficiente de '{record.accesorio_id.name}'. "
                            f"Disponible: {stock.cantidad_disponible}, Solicitado: {record.cantidad}"
                        )
                    stock.cantidad_disponible -= record.cantidad
                elif record.tipo_movimiento == 'ajuste':
                    # Ajuste: ajustar a cantidad específica (la cantidad del movimiento es el delta)
                    stock.cantidad_disponible += record.cantidad
            except ValidationError:
                raise
            except Exception:
                _logger.exception('Error al actualizar stock para movimiento %s', record.id)
        
        return records

    # ==========================================================================
    # Display
    # ==========================================================================
    def name_get(self):
        """Muestra descripción legible del movimiento."""
        result = []
        for record in self:
            tipo_label = dict(record._fields['tipo_movimiento'].selection).get(record.tipo_movimiento, '')
            name = f"{record.accesorio_id.name} - {tipo_label} ({record.cantidad})"
            result.append((record.id, name))
        return result
