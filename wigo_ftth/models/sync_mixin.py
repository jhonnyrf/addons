# -*- coding: utf-8 -*-
from odoo import models, api


class FtthSyncMixin(models.AbstractModel):
    _name = 'wigo.ftth.sync.mixin'
    _description = 'Mixin para sincronización bidireccional subinterface ⇄ box.port'

    # =========================
    # Public API
    # =========================
    @api.model
    def _sync_link(self, subinterface, box_port):
        """Crea o reemplaza el enlace entre subinterface y box_port."""

        # Liberar relaciones previas
        self._unlink_previous_relations(subinterface, box_port)

        # Crear nuevo enlace
        if subinterface and box_port:
            self._link(subinterface, box_port)

    @api.model
    def _sync_unlink(self, subinterface=None, box_port=None):
        """Rompe el enlace entre subinterface y box_port."""

        if subinterface:
            self._clear_subinterface(subinterface)

        if box_port:
            self._clear_box_port(box_port)

    # =========================
    # Private Methods
    # =========================
    def _unlink_previous_relations(self, subinterface, box_port):
        """Desvincula relaciones existentes antes de crear una nueva."""

        # Caso 1: box_port ya vinculado a otra subinterface
        if box_port and box_port.subinterface_id and box_port.subinterface_id != subinterface:
            self._clear_subinterface(box_port.subinterface_id)
            self._clear_box_port(box_port)

        # Caso 2: subinterface ya vinculada a otro box_port
        if subinterface and subinterface.box_port_id and subinterface.box_port_id != box_port:
            self._clear_box_port(subinterface.box_port_id)
            self._clear_subinterface(subinterface)

    def _link(self, subinterface, box_port):
        """Establece el enlace bidireccional."""

        box = box_port.box_id
        box_group = box.box_group_id if box else False

        subinterface.with_context(skip_sync=True).write({
            'box_port_id': box_port.id,
            'box_id': box.id if box else False,
            'box_group_id': box_group.id if box_group else False,
            'state': 'occupied',
        })

        box_port.with_context(skip_sync=True).write({
            'subinterface_id': subinterface.id,
            'state': 'occupied',
        })

    def _clear_subinterface(self, subinterface):
        """Libera una subinterface."""
        subinterface.with_context(skip_sync=True).write({
            'box_port_id': False,
            'box_id': False,
            'box_group_id': False,
            'state': 'free',
        })

    def _clear_box_port(self, box_port):
        """Libera un box_port."""
        box_port.with_context(skip_sync=True).write({
            'subinterface_id': False,
            'state': 'free',
        })