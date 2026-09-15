import { useEffect, useRef } from 'react'
import { useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'

export function useMinutaEditor({
  html,
  chave,
  editando,
}: {
  html: string
  chave: string
  editando: boolean
}) {
  const htmlRef = useRef(html)
  htmlRef.current = html

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: false,
        codeBlock: false,
        code: false,
        blockquote: false,
        horizontalRule: false,
      }),
      Underline,
      TextAlign.configure({
        types: ['paragraph'],
        alignments: ['left', 'center', 'right', 'justify'],
        defaultAlignment: 'justify',
      }),
      TextStyleKit.configure({
        backgroundColor: false,
        color: false,
        lineHeight: { types: ['paragraph', 'textStyle'] },
      }),
    ],
    content: html || '<p></p>',
    editable: editando,
    editorProps: {
      attributes: {
        class: 'tiptap',
        spellcheck: 'true',
      },
    },
  })

  useEffect(() => {
    editor?.setEditable(editando)
  }, [editando, editor])

  useEffect(() => {
    if (!editor || !htmlRef.current) {
      return
    }
    editor.commands.setContent(htmlRef.current)
  }, [chave, editor])

  return editor
}
