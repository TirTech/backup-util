set themesdir [file join [pwd] [file dirname [info script]]]
lappend auto_path $themesdir
package provide arc_custom 1.0
source [file join $themesdir arc_custom arc_custom.tcl]
