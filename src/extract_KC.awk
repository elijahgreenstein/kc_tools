# This program extracts observations from decks 118, 119, and 762 from the
# ICOADS. These three decks make up the Kobe Collection.
#
# This program returns the following IMMA fields, separated by commas:
#
# - C0-1 Year (field $1)
# - C0-2 Month ($2)
# - C0-3 Day ($3)
# - C0-4 Hour ($4)
# - C0-5 Latitude ($5)
# - C0-6 Longitude ($6)
# - C0-15 ID ($12)
# - C1-6 Deck ($16)

BEGIN { OFS=","; FIELDWIDTHS="4 2 2 4 5 6 3 1 1 4 2 9 2 63 10 3 *" }
{
    if ($16 == 118 || $16 == 119 || $16 == 762)
        print $1, $2, $3, $4, $5, $6, $12, $16
}
