#ifndef UTILS_H
#define UTILS_H

#define HASHSIZE	101

/*
 * Adds LNK to the start of LIST and
 * sets LIST to point to the new LNK.
 * `next` should be the first member of LNK
 * and of every link on LIST.
 */
#define ADD_LINK(LNK, LIST)	\
do {				\
	assert(LNK != NULL);	\
	LNK->next = LIST;	\
	LIST = LNK;		\
} while (0)

/*
 * Reverses the NULL terminated llist
 * and returns a pointer to its new
 * first element.
 * `next` should be the first member
 * of the links in llist.
 * In other words, *llist == llist->next.
 */
void *reverse_linked_list(void *llist);

char *strdup(const char *s);

char *extended_str(const char *base, const char *ext);

/*
 * Returns a pointer to the entry for
 * key in table, or NULL if table does
 * not contain an entry for key.
 * table should be an array of linked lists
 * of entries which have `next` for their
 * first member and `key` for their second
 * member:
 * struct entry {
 * 	struct entry *next;
 * 	const char *key;
 * 	...
 * };)
 * The size of table should be HASHSIZE,
 * which is defined in utils.h.
 */
void *look_up(const char *key, void *table);

/*
 * Creates a new entry in table for key.
 * The table must not have an existing
 * entry for the given key.
 * table should be an array of linked lists
 * of entries which have `next` for their
 * first member and `key` for their second
 * member:
 * struct entry {
 * 	void *next;
 * 	const char *key;
 * 	...
 * };)
 * The size of table should be HASHSIZE,
 * which is defined in utils.h.
 */
void *create_entry(const char *key, void *table);

#endif
