<?php
/**
 * Plugin Name: Meta Box Group (vervanger, demogemeente)
 * Description: Vervanger van de extensie Meta Box Group, die OpenPDC als afhankelijkheid
 *              controleert. De echte extensie staat alleen op wordpress.org en metabox.io,
 *              die vanuit deze omgeving niet bereikbaar zijn. Deze vervanger laat Meta Box
 *              velden van het type "group" als gewone tekstvelden zien; de REST-API van
 *              OpenPDC heeft hem niet nodig. Zet op een echte installatie de extensie zelf.
 * Version: 0.1.0
 * License: GPL-2.0-or-later
 */

defined('ABSPATH') || exit;

if (! class_exists('RWMB_Group')) {
    // Alleen de klasse die andere code soms controleert; geen eigen gedrag.
    class RWMB_Group
    {
    }
}
